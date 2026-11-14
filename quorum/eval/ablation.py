"""Ablation of the gate: which parts of the policy are doing the work (mentor correction 1.6).

Each variant removes one piece of the tender policy and replays the scripted episodes of
quorum/scenarios/tender/scripted.py with the gate enforcing. Deterministic and offline: no model
is called, so it measures the mechanism, not the agents.

For each variant and kind we report how many episodes leak the canary and how many publish the
right winner. A piece earns its place if removing it lets an attack through or breaks an honest
run; a piece whose removal changes nothing is either redundant or not exercised by the scripts
(quotas, for example, only matter against an agent that probes within_budget as an oracle,
which the scripts never do: we say so instead of claiming it).

Usage:
  uv run python -m quorum.eval.ablation            # prints the table
  uv run python -m quorum.eval.ablation --md       # the same table in Markdown
"""
from __future__ import annotations

import argparse
from dataclasses import replace

from ..domain import Policy
from ..domain.tools import Kind, Tool
from ..scenarios.tender import KINDS, POLICY, TOOLS
from ..scenarios.tender.scripted import evaluator_steps, publisher_steps, registrar_steps
from .baseline import prepare_injected

SEEDS = range(20261114, 20261134)


def _without_declassifiers(names: set[str]) -> tuple[Policy, tuple[Tool, ...]]:
    """The policy and the tools with `names` demoted to ordinary tools (their result keeps its label)."""
    tools = tuple(Tool(t.name, t.fn, t.description, t.params, Kind.NORMAL) if t.name in names else t
                  for t in TOOLS)
    return replace(POLICY, declassifiers=POLICY.declassifiers - names), tools


VARIANTS: dict[str, tuple[Policy, tuple[Tool, ...]]] = {
    "completa": (POLICY, TOOLS),
    "sin etiquetas restringidas (P1)": (replace(POLICY, restricted=()), TOOLS),
    "sin desclasificadores": _without_declassifiers(set(POLICY.declassifiers)),
    "sin transcribe": _without_declassifiers({"transcribe"}),
    "sin score_bids": _without_declassifiers({"score_bids"}),
    "sin within_budget": _without_declassifiers({"within_budget"}),
    "sin cuotas": (replace(POLICY, quotas={}), TOOLS),
}


def episode(kind: str, seed: int, variant: tuple[Policy, tuple[Tool, ...]]) -> dict:
    policy, tools = variant
    case = prepare_injected(seed, None, scanned=(kind == "honest_scanned"), policy=policy, tools=tools,
                            enforce=True)
    registrar, evaluator, publisher = (case.session(r) for r in ("registrar", "evaluator", "publisher"))
    registrar_steps(registrar, kind)
    evaluator_steps(evaluator, kind)
    publisher_steps(publisher, kind)
    return {"leak": case.leak, "useful": case.useful, "published": case.published}


def table(seeds=SEEDS) -> dict[str, dict[str, tuple[int, int, int]]]:
    """{variant: {kind: (episodes, leaks, useful)}}."""
    out = {}
    for name, variant in VARIANTS.items():
        row = {}
        for kind in KINDS:
            eps = [episode(kind, s, variant) for s in seeds]
            row[kind] = (len(eps), sum(e["leak"] for e in eps), sum(e["useful"] for e in eps))
        out[name] = row
    return out


def render(t, md: bool = False) -> str:
    head = ["variante", *(f"{k} fuga/útil" for k in KINDS)]
    rows = [[name, *(f"{leak}/{useful} de {n}" for n, leak, useful in r.values())] for name, r in t.items()]
    if md:
        return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head),
                          *("| " + " | ".join(r) + " |" for r in rows)])
    width = max(len(r[0]) for r in rows) + 2
    return "\n".join(r[0].ljust(width) + "  ".join(c.ljust(14) for c in r[1:]) for r in [head, *rows])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    a = ap.parse_args(argv)
    print(render(table(), md=a.md))


if __name__ == "__main__":
    main()
