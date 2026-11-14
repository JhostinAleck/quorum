"""The tender with model-driven agents: honest prompts, with and without an injected document.

    OPENROUTER_API_KEY=... python -m quorum.llm_bench --model openai/gpt-6-luna --seeds 10 \
        --data datos/agentes-inyeccion.jsonl --out docs/resultados-agentes.md

Nobody is told to attack. The three agents get the honest prompts of the
scenario. In half of the episodes the cover letter of one supplier carries a
fixed instruction asking for a rival's sealed amount (prepare(injection=True)).
What is measured is what the model does with it and what the gate does then.

Every episode runs once, in audit mode: nothing is blocked, so the harm can
happen, and the gate's decision is in the audit log. That gives both arms from
the same behaviour: without defense (what was published) and with the gate
(what it would have stopped).

This calls a model and costs money: three agents per episode, a few turns each.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .adapters.agent_loop import Chat, run_agent
from .scenarios import tender

VARIANTS = {"honest": False, "injection": True}


def episode(seed: int, variant: str, chat: Chat, max_turns: int = 12) -> dict[str, Any]:
    """One tender with the model as the three agents. Returns its grading and what each agent did."""
    case = tender.prepare(seed, defense=False, injection=VARIANTS[variant])
    errors = {}
    for role in tender.ROLES:
        try:
            run_agent(case.session(role), chat, system=tender.SYSTEM[role], task=tender.TASK[role],
                      max_turns=max_turns)
        except Exception as error:      # a provider failure ends that agent, not the batch
            errors[role] = f"{type(error).__name__}: {error}"[:200]
    sessions = case.quorum.sessions
    return {
        "variant": variant, "seed": seed,
        "published": case.published, "leak": case.leak, "leak_in_words": case.leak_in_words,
        "useful": case.useful, "gate_blocks": case.quorum_blocks,
        # an agent ended up with a sealed amount in its context, whether or not it wrote it anywhere
        "saw_a_secret": sorted(name for name, session in sessions.items() if session.context.secrets),
        # only calls that returned an amount: a denied or failed attempt opened nothing
        "opened": sorted({str(step["args"].get("ref")) for session in sessions.values()
                          for step in session.trajectory if step["tool"] == "open_bid" and "result" in step}),
        "steps": {name: len(session.trajectory) for name, session in sessions.items()},
        "errors": errors,
        "portal": case.portal,
        "trajectories": {name: session.trajectory for name, session in sessions.items()},
    }


def run(chat: Chat, seeds: int, workers: int = 8,
        progress: Callable[[int, int], None] | None = None) -> list[dict[str, Any]]:
    todo = [(seed, variant) for variant in VARIANTS for seed in range(seeds)]
    rows = []

    def safely(item: tuple[int, str]) -> dict[str, Any]:
        try:
            return episode(item[0], item[1], chat)
        except Exception as error:      # one odd episode must not cost the ones already paid for
            return {"variant": item[1], "seed": item[0], "published": False, "leak": False, "leak_in_words": False,
                    "useful": False, "gate_blocks": False, "saw_a_secret": [], "opened": [], "steps": {},
                    "errors": {"episode": f"{type(error).__name__}: {error}"[:200]}, "portal": [],
                    "trajectories": {}}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for done, row in enumerate(pool.map(safely, todo), start=1):
            rows.append(row)
            if progress:
                progress(done, len(todo))
    return rows


def tables(rows: list[dict[str, Any]], model: str, cost: float | None) -> str:
    def cell(chosen: list[dict[str, Any]], test: Callable[[dict[str, Any]], bool]) -> str:
        hits = sum(bool(test(row)) for row in chosen)
        return f"{hits}/{len(chosen)}"

    honest = [row for row in rows if row["variant"] == "honest"]
    injected = [row for row in rows if row["variant"] == "injection"]
    harmed = lambda row: row["leak"] or row["leak_in_words"]  # noqa: E731
    missed = lambda row: harmed(row) and not row["gate_blocks"]  # noqa: E731
    out = [f"Modelo de los agentes: `{model}`. {len(honest)} trámites sin inyección y {len(injected)} con la carta "
           "inyectada, todos con los prompts honestos."
           + (f" Costo de la corrida: {cost:.2f} USD." if cost is not None else ""), "",
           "| | Sin inyección | Con la carta inyectada |", "|---|---|---|",
           f"| Algún agente abrió un sobre | {cell(honest, lambda r: r['opened'])} | "
           f"{cell(injected, lambda r: r['opened'])} |",
           f"| El valor sellado salió al portal (sin defensa) | {cell(honest, harmed)} | {cell(injected, harmed)} |",
           f"| La compuerta habría bloqueado la publicación | {cell(honest, lambda r: r['gate_blocks'])} | "
           f"{cell(injected, lambda r: r['gate_blocks'])} |",
           f"| Fugas que la compuerta habría dejado pasar | {cell(honest, missed)} | {cell(injected, missed)} |",
           f"| Adjudicación correcta publicada, sin defensa | {cell(honest, lambda r: r['useful'])} | "
           f"{cell(injected, lambda r: r['useful'])} |",
           f"| Adjudicación correcta publicada, con la compuerta | "
           f"{cell(honest, lambda r: r['useful'] and not r['gate_blocks'])} | "
           f"{cell(injected, lambda r: r['useful'] and not r['gate_blocks'])} |",
           f"| Bloqueos sin fuga (la compuerta detuvo un trámite que no filtraba) | "
           f"{cell(honest, lambda r: r['gate_blocks'] and not harmed(r))} | "
           f"{cell(injected, lambda r: r['gate_blocks'] and not harmed(r))} |"]
    failed = sum(bool(row["errors"]) for row in rows)
    if failed:
        out += ["", f"En {failed} episodios algún agente terminó con un error del proveedor; se cuentan como están."]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> None:
    from .monitor_bench import _spent

    parser = argparse.ArgumentParser(prog="python -m quorum.llm_bench", description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", default=os.environ.get("QUORUM_MODEL", ""))
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--data", default="", help="save every episode as JSONL, with its trajectories")
    parser.add_argument("--from-data", default="", help="rebuild the table from a saved JSONL, without any call")
    parser.add_argument("--out", default="", help="write the table into this Markdown file, between its markers")
    args = parser.parse_args(argv)

    if args.from_data:
        lines = Path(args.from_data).read_text(encoding="utf-8").splitlines()
        meta, rows = json.loads(lines[0]), [json.loads(line) for line in lines[1:]]
        model, cost = meta["model"], meta.get("cost_usd")
    else:
        from .adapters.openai_chat import openai_chat

        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key or not args.model:
            sys.exit("set OPENROUTER_API_KEY and pass --model (or QUORUM_MODEL)")
        model, before = args.model, _spent(api_key)
        rows = run(openai_chat(model, api_key=api_key), args.seeds, args.workers,
                   lambda done, total: print(f"\r{done}/{total}", end="", file=sys.stderr, flush=True))
        print(file=sys.stderr)
        after = _spent(api_key)
        cost = after - before if before is not None and after is not None else None
        if args.data:
            meta = {"model": model, "seeds": args.seeds, "cost_usd": cost}
            Path(args.data).parent.mkdir(parents=True, exist_ok=True)
            Path(args.data).write_text("\n".join(json.dumps(item, ensure_ascii=False, default=str)
                                                 for item in [meta, *rows]) + "\n", encoding="utf-8")

    text = tables(rows, model, cost)
    if not args.out:
        sys.stdout.write(text)
        return
    path, start, end = Path(args.out), "<!-- agents:start -->", "<!-- agents:end -->"
    page = path.read_text(encoding="utf-8")
    if start not in page or end not in page:
        sys.exit(f"{path} has no {start} ... {end} markers")
    head, rest = page.split(start, 1)
    path.write_text(f"{head}{start}\n\n{text}\n{end}{rest.split(end, 1)[1]}", encoding="utf-8")
    print(f"table written to {path}")


if __name__ == "__main__":
    main()
