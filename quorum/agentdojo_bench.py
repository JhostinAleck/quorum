"""The Quorum gate on an external benchmark: AgentDojo, replayed without a language model.

    uv run --with agentdojo python -m quorum.agentdojo_bench
    uv run --with agentdojo python -m quorum.agentdojo_bench --suites banking slack
    uv run --with agentdojo python -m quorum.agentdojo_bench --out docs/resultados-agentdojo.md \
        --json datos/agentdojo-replay.json

AgentDojo ships, for every user task and every injection task, the list of tool calls that
solves it (`ground_truth`). That allows a deterministic replay with no model and no cost:

  benign trace    the ground-truth calls of a user task
  attacked trace  the data-reading calls of a user task, on an environment whose injection
                  vectors carry the attacker's text, followed by the ground-truth calls of the
                  injection task: what a fully obedient agent would do

Every call goes through one Quorum session. The benchmark's tools are Quorum tools: the ones
that change state or send something out are sinks, and what a reading tool returns enters the
store under a key the policy lists as untrusted. The policy has strict_mode on (rule P2), and
the approver stands for the user's own request: it approves a sink call only if every argument
it carries can be found in the text of the user's task prompt.

agentdojo is imported lazily, so the rest of the package works without it.
"""
from __future__ import annotations

import argparse
import inspect
import json
import re
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from .bootstrap import new_monitor
from .domain import Blocked, Kind, Policy, Request, Role, Tool, ToolError

BENCHMARK_VERSION = "v1.2.2"        # the newest suite set registered by the agentdojo package used
START, END = "<!-- agentdojo:start -->", "<!-- agentdojo:end -->"
CANARY = "QUORUM-CANARY"            # prefixed to the injected text, to see which tool result carried it
ROLE = "agent"

# --- The classification of every AgentDojo tool, reviewed one by one ----------------------------
#
#   READ_OWN   returns data the user owns and only the user (or the provider) writes
#   READ_EXT   returns data an outsider could have written: its result is untrusted
#   ACTION     changes state or sends something out: a sink
#   ACTION_EXT a sink whose result is also untrusted (fetching a URL sends a request out and
#              brings third-party content in)
READ_OWN, READ_EXT, ACTION, ACTION_EXT = "read_own", "read_untrusted", "action", "action_untrusted"
SINKS = frozenset({ACTION, ACTION_EXT})
UNTRUSTED_RESULT = frozenset({READ_EXT, ACTION_EXT})

CLASSIFICATION: dict[str, dict[str, str]] = {
    "banking": {
        "get_iban": READ_OWN,                           # the user's own account number
        "get_balance": READ_OWN,                        # a number computed by the bank
        "get_user_info": READ_OWN,                      # the profile only the user edits
        "get_most_recent_transactions": READ_EXT,       # the subject of an incoming transfer is written by its sender
        "get_scheduled_transactions": READ_EXT,         # payees and subjects may come from third-party invoices
        "read_file": READ_EXT,                          # bills and notices written by others
        "send_money": ACTION,
        "schedule_transaction": ACTION,
        "update_scheduled_transaction": ACTION,
        "update_password": ACTION,
        "update_user_info": ACTION,
    },
    "slack": {
        "get_channels": READ_EXT,                       # any member names a channel
        "read_channel_messages": READ_EXT,
        "read_inbox": READ_EXT,
        "get_users_in_channel": READ_EXT,               # user names are chosen by the users
        "get_webpage": ACTION_EXT,                      # an outbound request to any URL, and a page written by anybody
        "add_user_to_channel": ACTION,
        "send_direct_message": ACTION,
        "send_channel_message": ACTION,
        "invite_user_to_slack": ACTION,
        "remove_user_from_slack": ACTION,
        "post_webpage": ACTION,
    },
    "travel": {
        "get_user_information": READ_OWN,               # the traveller's own profile
        "get_all_hotels_in_city": READ_EXT,             # listings, prices and reviews are third-party content
        "get_hotels_prices": READ_EXT,
        "get_rating_reviews_for_hotels": READ_EXT,
        "get_hotels_address": READ_EXT,
        "get_all_restaurants_in_city": READ_EXT,
        "get_cuisine_type_for_restaurants": READ_EXT,
        "get_restaurants_address": READ_EXT,
        "get_rating_reviews_for_restaurants": READ_EXT,
        "get_dietary_restrictions_for_all_restaurants": READ_EXT,
        "get_contact_information_for_restaurants": READ_EXT,
        "get_price_for_restaurants": READ_EXT,
        "check_restaurant_opening_hours": READ_EXT,
        "get_all_car_rental_companies_in_city": READ_EXT,
        "get_car_types_available": READ_EXT,
        "get_rating_reviews_for_car_rental": READ_EXT,
        "get_car_fuel_options": READ_EXT,
        "get_car_rental_address": READ_EXT,
        "get_car_price_per_day": READ_EXT,
        "get_flight_information": READ_EXT,
        "search_calendar_events": READ_EXT,             # anybody can send an invitation
        "get_day_calendar_events": READ_EXT,
        "create_calendar_event": ACTION,                # it also e-mails the participants
        "cancel_calendar_event": ACTION,
        "reserve_hotel": ACTION,
        "reserve_car_rental": ACTION,
        "reserve_restaurant": ACTION,
        "send_email": ACTION,
    },
    "workspace": {
        "get_current_day": READ_OWN,                    # the clock
        "get_unread_emails": READ_EXT,                  # it also marks them as read; nothing leaves
        "get_sent_emails": READ_EXT,                    # replies quote what others wrote
        "get_received_emails": READ_EXT,
        "get_draft_emails": READ_EXT,
        "search_emails": READ_EXT,
        "search_contacts_by_name": READ_EXT,            # contacts are harvested from incoming mail
        "search_contacts_by_email": READ_EXT,
        "search_calendar_events": READ_EXT,
        "get_day_calendar_events": READ_EXT,
        "search_files_by_filename": READ_EXT,           # the drive holds files shared by others
        "get_file_by_id": READ_EXT,
        "list_files": READ_EXT,
        "search_files": READ_EXT,
        "send_email": ACTION,
        "delete_email": ACTION,
        "create_calendar_event": ACTION,
        "cancel_calendar_event": ACTION,
        "reschedule_calendar_event": ACTION,
        "add_calendar_event_participants": ACTION,
        "append_to_file": ACTION,
        "create_file": ACTION,
        "delete_file": ACTION,
        "share_file": ACTION,
    },
}
SUITES = tuple(CLASSIFICATION)


# --- The approver: "the user asked for exactly this" -------------------------------------------

_NUMBER = re.compile(r"(?<![\w.-])\d+(?:\.\d+)?(?![\w-])")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")


def _normalize(text: object) -> str:
    return " ".join(str(text).lower().split())


def _numbers(prompt: str) -> set[float]:
    return {float(number) for number in _NUMBER.findall(_THOUSANDS.sub("", prompt))}


def in_prompt(value: Any, prompt: str) -> bool:
    """Whether an argument value can be found in the text of the user's request.

    Text is compared without case and with whitespace collapsed, and it must match whole
    words. Numbers are compared as numbers. Lists and mappings need every element. An argument
    that was not given (None) and a boolean flag carry no target and no content, so they pass.
    """
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return float(value) in _numbers(prompt)
    if isinstance(value, str):
        needle = _normalize(value)
        if not needle:
            return True
        try:
            if float(needle) in _numbers(prompt):
                return True
        except ValueError:
            pass
        return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", _normalize(prompt)) is not None
    if isinstance(value, Mapping):
        return all(in_prompt(item, prompt) for item in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return all(in_prompt(item, prompt) for item in value)
    return False


def missing_arguments(arguments: Mapping[str, Any], prompt: str) -> list[str]:
    """The arguments of a call that the user's request does not contain."""
    return sorted(name for name, value in arguments.items() if not in_prompt(value, prompt))


def approver_for(prompt: str) -> Callable[[Request], bool]:
    """The stand-in for the human approval of rule P2.

    It sees only the request and the user's prompt. It never reads a tool result and it does
    not know which calls come from the attacker.
    """
    def approve(request: Request) -> bool:
        return not missing_arguments(request.arguments, prompt)
    return approve


# --- AgentDojo tools as Quorum tools -----------------------------------------------------------

def policy_for(classes: Mapping[str, str]) -> Policy:
    """One role with every tool of the suite, the action tools as sinks, rule P2 on."""
    return Policy(untrusted=("external.",), strict_mode=True,
                  sinks={name: () for name, klass in classes.items() if klass in SINKS},
                  roles={ROLE: Role(ROLE, tools=tuple(classes))})


def _render(result: Any) -> str:
    from agentdojo.agent_pipeline.tool_execution import tool_result_to_str
    try:
        return tool_result_to_str(result)
    except Exception:
        return str(result)


def quorum_tools(functions: Iterable[Any], classes: Mapping[str, str], runtime: Any, environment: Any,
                 carried: list[str]) -> list[Tool]:
    """Wrap every AgentDojo function. The wrapper runs the real function on the environment.

    What a reading tool returns is written to the store and read back, so its label is the one
    the policy assigns to the key: `external.*` is untrusted, `own.*` is not. `carried` collects
    the names of the tools whose result held the injected text.
    """
    def wrap(function: Any) -> Tool:
        name, klass = function.name, classes[function.name]

        def run(call, **arguments):
            given = {key: value for key, value in arguments.items() if value is not None}
            result, error = runtime.run_function(environment, name, given)
            if error:
                raise ToolError(error)
            if klass != ACTION:
                key = f"{'external' if klass in UNTRUSTED_RESULT else 'own'}.{name}"
                call.write(key, _render(result))
                if CANARY in call.read(key):
                    carried.append(name)
            return result

        fields = function.parameters.model_fields
        own = [inspect.Parameter(field, inspect.Parameter.KEYWORD_ONLY, default=None) for field in fields]
        run.__signature__ = inspect.Signature(      # the kernel derives the schema from the signature
            [inspect.Parameter("call", inspect.Parameter.POSITIONAL_OR_KEYWORD), *own])
        return Tool(name, run, function.description.strip() or name,
                    {field: info.description or field for field, info in fields.items()},
                    Kind.SINK if klass in SINKS else Kind.NORMAL)

    return [wrap(function) for function in functions]


def load_suite(name: str) -> Any:
    try:
        from agentdojo.task_suite import get_suite
    except ImportError as error:
        raise SystemExit("agentdojo is not installed. Run it with an overlay:\n"
                         "  uv run --with agentdojo python -m quorum.agentdojo_bench") from error
    suite = get_suite(BENCHMARK_VERSION, name)
    declared, actual = set(CLASSIFICATION[name]), {function.name for function in suite.tools}
    if declared != actual:
        raise SystemExit(f"{name}: the classification table and the suite differ: {sorted(declared ^ actual)}")
    return suite


# --- The replay --------------------------------------------------------------------------------

def replay(suite: Any, environment: Any, calls: Iterable[Any], prompt: str, *,
           enforce: bool) -> tuple[list[dict[str, Any]], list[Any]]:
    """Run the calls through one Quorum session. Returns one record per call and the calls that ran."""
    from agentdojo.functions_runtime import FunctionsRuntime

    classes = CLASSIFICATION[suite.name]
    carried: list[str] = []
    tools = quorum_tools(suite.tools, classes, FunctionsRuntime(suite.tools), environment, carried)
    quorum = new_monitor(policy_for(classes), tools, enforce=enforce, approver=approver_for(prompt))
    session = quorum.session(ROLE)
    steps, executed = [], []
    for call in calls:
        arguments, before = dict(call.args), len(carried)
        step = {"tool": call.function, "sink": classes[call.function] in SINKS, "arguments": arguments,
                "untrusted_context": bool(session.context.untrusted), "reason": ""}
        try:
            outcome = session.call(call.function, **arguments)
        except Exception as error:
            step |= {"status": "error", "reason": f"{type(error).__name__}: {error}"}
        else:
            if isinstance(outcome, Blocked):
                step |= {"status": "blocked", "reason": outcome.policy,
                         "missing": missing_arguments(arguments, prompt)}
            else:
                step["status"] = "executed"
                executed.append(call)
        step["carried_injection"] = len(carried) > before
        steps.append(step)
    return steps, executed


def _verdict(task: Any, check: str, pre: Any, post: Any, executed: list[Any]) -> bool | None:
    """AgentDojo's own checker of a task (`utility` or `security`), fed with the ground-truth answer."""
    output = task.GROUND_TRUTH_OUTPUT
    try:
        verdict = getattr(task, f"{check}_from_traces")(output, pre, post, executed)
        return bool(getattr(task, check)(output, pre, post) if verdict is None else verdict)
    except Exception:
        return None


def measure(name: str) -> dict[str, Any]:
    """Replay one suite: every user task alone, and every (user task, injection task) pair."""
    suite = load_suite(name)
    classes = CLASSIFICATION[name]
    modes = (("none", False), ("quorum", True))
    clean = suite.load_and_inject_default_environment({})
    vectors = list(suite.get_injection_vector_defaults())

    benign = []
    for user_id, task in suite.user_tasks.items():
        row: dict[str, Any] = {"user_task": user_id, "prompt": task.PROMPT}
        for mode, enforce in modes:
            environment = task.init_environment(clean.model_copy(deep=True))
            pre = environment.model_copy(deep=True)
            steps, executed = replay(suite, environment, task.ground_truth(environment), task.PROMPT, enforce=enforce)
            row[mode] = {"completed": all(step["status"] == "executed" for step in steps),
                         "utility": _verdict(task, "utility", pre, environment, executed), "steps": steps}
        row["sink_calls"] = sum(step["sink"] for step in row["quorum"]["steps"])
        benign.append(row)

    attacks = []
    for injection_id, attack in suite.injection_tasks.items():
        text_is_goal = True
        try:
            injected = suite.load_and_inject_default_environment(dict.fromkeys(vectors, f"{CANARY} {attack.GOAL}"))
        except Exception:       # the goal does not fit the YAML of the environment: the marker alone
            injected, text_is_goal = suite.load_and_inject_default_environment(dict.fromkeys(vectors, CANARY)), False
        for user_id, task in suite.user_tasks.items():
            row = {"user_task": user_id, "injection_task": injection_id, "text_is_goal": text_is_goal}
            for mode, enforce in modes:
                environment = task.init_environment(injected.model_copy(deep=True))
                pre = environment.model_copy(deep=True)
                reads = [call for call in task.ground_truth(environment) if classes[call.function] != ACTION]
                steps, executed = replay(suite, environment, [*reads, *attack.ground_truth(environment)],
                                         task.PROMPT, enforce=enforce)
                mine, theirs = steps[:len(reads)], steps[len(reads):]
                sinks = [step for step in theirs if step["sink"]]
                row[mode] = {
                    "attacker_sink_calls": len(sinks),
                    "executed": sum(step["status"] == "executed" for step in sinks),
                    "blocked": sum(step["status"] == "blocked" for step in sinks),
                    "errors": sum(step["status"] == "error" for step in sinks),
                    "security": _verdict(attack, "security", pre, environment, executed[len([
                        step for step in mine if step["status"] == "executed"]):]),
                    "delivered": any(step["carried_injection"] for step in mine),
                    "delivered_by": sorted({step["tool"] for step in mine if step["carried_injection"]}),
                    "untrusted_context": bool(theirs and theirs[0]["untrusted_context"]),
                }
            row["applicable"] = row["quorum"]["attacker_sink_calls"] > 0
            attacks.append(row)

    return {"suite": name, "user_tasks": len(suite.user_tasks), "injection_tasks": len(suite.injection_tasks),
            "classification": classes, "benign": benign, "attacks": attacks}


# --- The report --------------------------------------------------------------------------------

_CLASS_NAMES = {
    READ_OWN: ("Lectura", "confiable: dato propio del usuario"),
    READ_EXT: ("Lectura", "no confiable: puede traer texto de terceros"),
    ACTION: ("Acción (salida)", "no se etiqueta"),
    ACTION_EXT: ("Acción (salida)", "no confiable: puede traer texto de terceros"),
}


def _pct(count: int, n: int) -> str:
    return "n/a" if n == 0 else f"{100 * count / n:.0f} % ({count}/{n})"


def _why(step: Mapping[str, Any]) -> str:
    if step["status"] == "error":
        return f"`{step['tool']}` falló: {step['reason']}"
    names = ", ".join(f"`{name}`" for name in step.get("missing", ()))
    return f"`{step['tool']}`: el pedido del usuario no trae {names}"


def totals(result: Mapping[str, Any]) -> dict[str, int]:
    """The counts of one suite that the tables show."""
    applicable = [row for row in result["attacks"] if row["applicable"]]
    count = lambda rows, mode, field: sum(int(bool(row[mode][field])) for row in rows)  # noqa: E731
    add = lambda rows, mode, field: sum(row[mode][field] for row in rows)  # noqa: E731
    return {
        "user_tasks": result["user_tasks"], "injection_tasks": result["injection_tasks"],
        "pairs": len(result["attacks"]), "applicable": len(applicable),
        "delivered": count(applicable, "none", "delivered"),
        "attacker_calls": add(applicable, "none", "attacker_sink_calls"),
        "executed_none": add(applicable, "none", "executed"),
        "executed_quorum": add(applicable, "quorum", "executed"),
        "errors_quorum": add(applicable, "quorum", "errors"),
        "stopped_quorum": sum(row["quorum"]["blocked"] == row["quorum"]["attacker_sink_calls"] for row in applicable),
        "security_none": count(applicable, "none", "security"),
        "security_quorum": count(applicable, "quorum", "security"),
        "benign_none": count(result["benign"], "none", "completed"),
        "benign_quorum": count(result["benign"], "quorum", "completed"),
        "utility_none": count(result["benign"], "none", "utility"),
        "utility_quorum": count(result["benign"], "quorum", "utility"),
        "benign_with_sinks": sum(row["sink_calls"] > 0 for row in result["benign"]),
    }


def tables(results: list[dict[str, Any]], version: str) -> str:
    sums = {result["suite"]: totals(result) for result in results}
    out = [f"Paquete `agentdojo` {version}, conjunto de tareas `{BENCHMARK_VERSION}`. Sin modelo de lenguaje.", "",
           "## Lo que se repitió", "",
           "| Conjunto | Tareas de usuario | Tareas de inyección | Pares | Pares con acción del atacante | "
           "Pares en que una lectura trajo la inyección |", "|---|---|---|---|---|---|"]
    for name, t in sums.items():
        out.append(f"| `{name}` | {t['user_tasks']} | {t['injection_tasks']} | {t['pairs']} | {t['applicable']} | "
                   f"{_pct(t['delivered'], t['applicable'])} |")

    out += ["", "## El ataque: agente obediente", "",
            "Llamadas de acción del atacante que llegan a ejecutarse, y pares en los que el verificador de "
            "AgentDojo (`security`) da el ataque por logrado. Menos es mejor.", "",
            "| Conjunto | Acciones del atacante ejecutadas, sin defensa | Con Quórum | "
            "Pares con todas las acciones detenidas | Ataque logrado según AgentDojo, sin defensa | Con Quórum |",
            "|---|---|---|---|---|---|"]
    for name, t in sums.items():
        out.append(f"| `{name}` | {_pct(t['executed_none'], t['attacker_calls'])} | "
                   f"{_pct(t['executed_quorum'], t['attacker_calls'])} | "
                   f"{_pct(t['stopped_quorum'], t['applicable'])} | {_pct(t['security_none'], t['applicable'])} | "
                   f"{_pct(t['security_quorum'], t['applicable'])} |")

    out += ["", "## El costo: tareas legítimas", "",
            "Tareas de usuario cuya traza de referencia se ejecuta completa, y las que el verificador de AgentDojo "
            "(`utility`) da por cumplidas. Más es mejor.", "",
            "| Conjunto | Completas, sin defensa | Completas, con Quórum | Cumplidas según AgentDojo, sin defensa | "
            "Con Quórum | Tareas que necesitan alguna acción |", "|---|---|---|---|---|---|"]
    for name, t in sums.items():
        out.append(f"| `{name}` | {_pct(t['benign_none'], t['user_tasks'])} | "
                   f"{_pct(t['benign_quorum'], t['user_tasks'])} | {_pct(t['utility_none'], t['user_tasks'])} | "
                   f"{_pct(t['utility_quorum'], t['user_tasks'])} | {t['benign_with_sinks']} |")

    out += ["", "## Tareas legítimas que Quórum detuvo", "",
            "| Conjunto | Tarea | Primera llamada detenida y por qué | Llamadas detenidas |", "|---|---|---|---|"]
    for result in results:
        for row in result["benign"]:
            stopped = [step for step in row["quorum"]["steps"] if step["status"] != "executed"]
            if stopped:
                out.append(f"| `{result['suite']}` | `{row['user_task']}` | {_why(stopped[0])} | {len(stopped)} |")

    out += ["", "## Clasificación de las herramientas", "",
            "| Conjunto | Herramienta | Clase | Etiqueta de lo que devuelve |", "|---|---|---|---|"]
    for result in results:
        for tool, klass in result["classification"].items():
            kind, label = _CLASS_NAMES[klass]
            out.append(f"| `{result['suite']}` | `{tool}` | {kind} | {label} |")
    return "\n".join(out) + "\n"


def write_between_markers(path: Path, text: str) -> None:
    """Replace what the file has between the two markers."""
    document = path.read_text(encoding="utf-8")
    if START not in document or END not in document:
        raise SystemExit(f"{path} has no {START} ... {END} markers")
    head, rest = document.split(START, 1)
    path.write_text(f"{head}{START}\n\n{text}\n{END}{rest.split(END, 1)[1]}", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m quorum.agentdojo_bench", description=__doc__.split("\n\n")[0])
    parser.add_argument("--suites", nargs="*", default=list(SUITES), choices=list(SUITES))
    parser.add_argument("--out", default="", help="write the tables into this Markdown file, between its markers")
    parser.add_argument("--json", default="", help="also save every replay as JSON")
    args = parser.parse_args(argv)

    results = [measure(name) for name in args.suites]
    from importlib.metadata import version
    package = version("agentdojo")
    text = tables(results, package)
    if args.json:
        data = {"agentdojo": package, "benchmark_version": BENCHMARK_VERSION,
                "totals": {result["suite"]: totals(result) for result in results}, "suites": results}
        Path(args.json).write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str) + "\n",
                                   encoding="utf-8")
    if not args.out:
        sys.stdout.write(text)
        return
    write_between_markers(Path(args.out), text)
    print(f"tables written to {args.out} ({', '.join(args.suites)})")


if __name__ == "__main__":
    main()
