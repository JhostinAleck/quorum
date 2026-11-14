"""Entry points for running Quorum as separate processes.

    python -m quorum.launch monitor ...   the monitor service: the only one with the store and the audit log
    python -m quorum.launch agent ...     one agent: it only knows the monitor's URL and its own token
    python -m quorum.launch report ...    the operator: reads how the episode went

Each one is meant to run in its own container. This module is a composition
root, like bootstrap.py: the only place that knows the scenario, the adapters
and the infrastructure at the same time.

Secrets come from the environment, never from the command line, so they do not
show up in process listings.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from typing import Any

SCENARIOS = ("tender",)
MODES = ("scripted", "llm")


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"missing environment variable {name}")
    return value


def _wait_until_healthy(url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            with urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            pass
        if time.monotonic() >= deadline:
            sys.exit(f"the monitor at {url} did not become healthy in {timeout:.0f} s")
        time.sleep(0.2)


def _stop_on_sigterm() -> None:
    # as PID 1 in a container, a signal with the default action is ignored: install a handler
    def stop(*_: Any) -> None:
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)


def monitor(args: argparse.Namespace) -> None:
    from . import integrity
    from .adapters.http_server import MonitorServer
    from .infrastructure import SQLiteStore
    from .scenarios import tender

    if not args.unpinned and not integrity.pinned(args.scenario):
        sys.exit("error: the policy, the tools or the code are not the ones pinned in quorum/integrity.lock.json:\n  "
                 + "\n  ".join(integrity.check())
                 + "\nrun `python -m quorum.integrity --write` and commit the lock if the change is intended, "
                 "or pass --unpinned to run anyway")
    tokens = {_env(f"QUORUM_TOKEN_{role.upper()}"): role for role in tender.ROLES}
    admin_token = _env("QUORUM_ADMIN_TOKEN")
    store = None
    if args.store:
        if os.path.exists(args.store):      # every start is a fresh episode
            os.remove(args.store)
        store = SQLiteStore(args.store)
    case = tender.prepare(args.seed, defense=not args.audit, scanned=args.scanned, injection=args.injection,
                          store=store)
    # sealed before the server exists: no agent can act before the log says what is deciding
    found = integrity.seal(case.quorum, args.scenario, expected=os.environ.get("QUORUM_EXPECT_PIPELINE", "").strip())

    def grading() -> dict[str, Any]:
        return {"scenario": args.scenario, "seed": args.seed, "enforce": not args.audit,
                "integrity": {**found, "pinned": not args.unpinned},
                "published": case.published, "leak": case.leak, "useful": case.useful,
                "quorum_blocks": case.quorum_blocks}

    server = MonitorServer(case.quorum, tokens, admin_token=admin_token, host=args.host, port=args.port,
                           extra_state=grading)
    _stop_on_sigterm()
    mode = "audit only" if args.audit else "enforcing"
    print(f"quorum monitor listening on {server.url} ({args.scenario}, seed {args.seed}, {mode}, "
          f"pipeline {found['pipeline'][:16]})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


def agent(args: argparse.Namespace) -> None:
    from .adapters.http_client import RemoteSession

    token = _env("QUORUM_TOKEN")
    _wait_until_healthy(args.url)
    session = RemoteSession(args.url, token)
    if session.role != args.role:           # the identity comes from the token, not from the flag
        sys.exit(f"this token belongs to the role {session.role!r}, not to {args.role!r}")

    if args.mode == "scripted":
        from .scenarios.tender.scripted import KINDS, ROLE_STEPS

        if args.kind not in KINDS:
            sys.exit(f"unknown episode kind {args.kind!r}: choose one of {', '.join(KINDS)}")
        ROLE_STEPS[args.role](session, args.kind)
        summary = {"role": args.role, "mode": "scripted", "kind": args.kind}
    else:
        from .adapters.agent_loop import run_agent
        from .adapters.openai_chat import openai_chat
        from .scenarios.tender.prompts import SYSTEM, TASK

        model = args.model or os.environ.get("QUORUM_MODEL", "").strip()
        if not model:
            sys.exit("llm mode needs a model: pass --model or set QUORUM_MODEL")
        chat = openai_chat(model, api_key=_env("OPENROUTER_API_KEY"))
        messages = run_agent(session, chat, system=SYSTEM[args.role], task=TASK[args.role],
                             max_turns=args.max_turns)
        calls = sum(len(m.get("tool_calls") or ()) for m in messages if m.get("role") == "assistant")
        summary = {"role": args.role, "mode": "llm", "model": model, "tool_calls": calls}
    print(json.dumps(summary, ensure_ascii=False), flush=True)


def report(args: argparse.Namespace) -> None:
    from . import integrity
    from .adapters.http_client import RemoteAdmin

    admin_token = _env("QUORUM_ADMIN_TOKEN")
    _wait_until_healthy(args.url)
    state = RemoteAdmin(args.url, admin_token).state()
    declared = {k: v for k, v in (state.get("extra", {}).get("integrity") or {}).items() if k != "pinned"}
    # what the monitor says it runs must be what it sealed in the log before the first call
    sealed = bool(declared) and integrity.sealed(state["audit_log"]) == declared
    summary = {
        **state.get("extra", {}),
        "integrity_sealed": sealed,
        "audit_log_valid": state["audit_log_valid"],
        "audit_log_events": len(state["audit_log"]),
        "steps": {principal: len(steps) for principal, steps in state["trajectories"].items()},
        "publications": [emission["arguments"] for emission in state["emissions"]],
        "blocks": [{"principal": event["principal"], "tool": event["tool"],
                    "policy": event["decision"]["policy"], "reason": event["decision"]["reason"]}
                   for event in state["blocks"]],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    if not state["audit_log_valid"] or not sealed:
        sys.exit(1)


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(prog="python -m quorum.launch", description=__doc__.split("\n\n")[0])
    commands = main.add_subparsers(dest="command", required=True)

    m = commands.add_parser("monitor", help="run the monitor service")
    m.add_argument("--scenario", choices=SCENARIOS, default="tender")
    m.add_argument("--seed", type=int, default=1)
    m.add_argument("--scanned", action="store_true", help="one bid arrives as a scan")
    m.add_argument("--injection", action="store_true", help="one cover letter carries an instruction for the agents")
    m.add_argument("--audit", action="store_true", help="the gate only audits: nothing is blocked")
    m.add_argument("--host", default="127.0.0.1")
    m.add_argument("--port", type=int, default=8080)
    m.add_argument("--store", default="", help="path of a SQLite store (default: in memory)")
    m.add_argument("--unpinned", action="store_true",
                   help="start even if the policy, the tools or the code differ from quorum/integrity.lock.json")
    m.set_defaults(run=monitor)

    a = commands.add_parser("agent", help="run one agent against a remote monitor")
    a.add_argument("--role", required=True)
    a.add_argument("--url", required=True)
    a.add_argument("--mode", choices=MODES, default="scripted")
    a.add_argument("--kind", default="honest", help="scripted episode kind (scripted mode only)")
    a.add_argument("--model", default="", help="model id for llm mode (or QUORUM_MODEL)")
    a.add_argument("--max-turns", type=int, default=12)
    a.set_defaults(run=agent)

    r = commands.add_parser("report", help="print how the episode went")
    r.add_argument("--url", required=True)
    r.set_defaults(run=report)
    return main


def main(argv: list[str] | None = None) -> None:
    from .domain import QuorumError

    args = parser().parse_args(argv)
    try:
        args.run(args)
    except QuorumError as error:            # a clean message and a non-zero exit, never a traceback
        sys.exit(f"error: {error}")


if __name__ == "__main__":
    main()
