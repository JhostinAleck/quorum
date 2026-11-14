"""The same gate on several domains, measured the same way.

    python -m quorum.bench                 prints the tables
    python -m quorum.bench --seeds 500     more episodes per kind
    python -m quorum.bench --out docs/resultados-dominios.md

Every episode is scripted: no language model, no cost, same result on every
machine. So this measures the mechanism (does the gate stop the flow, what does
it cost, does it need changes per domain), not how often a model misbehaves.

Three defenses are compared on the same episodes:

  none        nothing is checked
  exact match a filter that knows every secret and blocks an output that carries
              one verbatim to somebody who may not have it. It is what one would
              build first, and it never blocks honest work
  Quorum      the provenance gate, with the policy file of the domain

Each kind of episode runs twice per seed: once in audit mode, where nothing is
blocked and the harm can happen, and once enforcing, to see what is left.
"""
from __future__ import annotations

import argparse
import importlib
import json
import statistics
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DOMAINS = {     # module -> how the documents call it
    "tender": "Licitación pública",
    "helpdesk": "Mesa de ayuda",
    "clinic": "Historias clínicas",
    "bank": "Banca",
    "lawfirm": "Sector legal",
}
KERNEL = ("domain", "application", "infrastructure")


def harmed(episode: Any) -> bool:
    """Something that must not happen did: a secret reached the wrong place, in any form, or money moved."""
    return bool(episode.leak or getattr(episode, "leak_in_words", False) or getattr(episode, "hijacked", False))


def group(kind: str) -> str:
    if kind == "honest_careless":
        return "careless"
    if kind.startswith("honest"):
        return "honest"
    return "injection" if kind == "injection" else "attack"


@dataclass
class Row:
    """One kind of episode over all seeds. Every field counts episodes."""
    domain: str
    kind: str
    group: str          # honest, careless, attack, disguised, injection
    n: int = 0
    harm_none: int = 0          # harm with no defense
    harm_exact: int = 0         # harm left by the exact-match filter
    harm_quorum: int = 0        # harm left by the gate
    useful_none: int = 0
    useful_quorum: int = 0
    blocked_quorum: int = 0     # episodes in which the gate stopped something


def measure(domain: str, seeds: Iterable[int]) -> list[Row]:
    module = importlib.import_module(f"quorum.scenarios.{domain}")
    rows = []
    for kind in module.KINDS:
        variants = [(group(kind), False)]
        if kind.startswith("attack_k"):
            variants.append(("disguised", True))    # the same attack, with the secret spelled out
        for name, disguise in variants:
            row = Row(domain, kind, name)
            options = {"disguise": True} if disguise else {}
            for seed in seeds:
                audited = module.run(kind, seed, defense=False, **options)
                enforced = module.run(kind, seed, defense=True, **options)
                row.n += 1
                row.harm_none += harmed(audited)
                # the filter stops the episode only if a secret left verbatim; whatever else happened, happened
                row.harm_exact += harmed(audited) and not audited.leak
                row.harm_quorum += harmed(enforced)
                row.useful_none += bool(audited.useful)
                row.useful_quorum += bool(enforced.useful)
                row.blocked_quorum += bool(enforced.quorum_blocks)
            rows.append(row)
    return rows


def decision_time(domain: str) -> float:
    """Median time of one gate decision, in microseconds, on the last sink call of an attack."""
    from quorum.domain.gate import Request, evaluate
    from quorum.domain.labels import Label

    module = importlib.import_module(f"quorum.scenarios.{domain}")
    kind = next(k for k in module.KINDS if k.startswith("attack_k"))
    quorum = module.run(kind, 1, defense=False).case.quorum
    event = quorum.blocks()[-1]
    label = Label(frozenset(event["label_before"]["secrets"]), frozenset(event["label_before"]["untrusted"]))
    request = Request(event["principal"], event["role"], event["tool"], event["args"], label)
    samples = []
    for _ in range(200):
        start = time.perf_counter()
        for _ in range(50):
            evaluate(request, quorum.policy)
        samples.append((time.perf_counter() - start) / 50 * 1e6)
    return statistics.median(samples)


def size(domain: str) -> dict[str, int]:
    """What a domain is made of: lines of its policy file and of its tools."""
    folder = Path(__file__).parent / "scenarios" / domain

    def lines(name: str) -> int:
        text = (folder / name).read_text(encoding="utf-8")
        return sum(1 for line in text.splitlines() if line.strip() and not line.strip().startswith("#"))

    return {"policy": lines("policy.toml"), "tools": lines("tools.py")}


def summarize(rows: list[Row]) -> dict[str, dict[str, Any]]:
    """Per domain and group: the counts added up over kinds."""
    summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        cell = summary.setdefault(row.domain, {}).setdefault(row.group, Row(row.domain, "*", row.group))
        for field in ("n", "harm_none", "harm_exact", "harm_quorum", "useful_none", "useful_quorum", "blocked_quorum"):
            setattr(cell, field, getattr(cell, field) + getattr(row, field))
    return summary


def _dec(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")      # the documents are in Spanish


def _pct(count: int, n: int) -> str:
    return "n/a" if n == 0 else f"{100 * count / n:.0f} % ({count}/{n})"


def report(domains: list[str], seeds: int) -> tuple[str, dict[str, Any]]:
    rows = [row for domain in domains for row in measure(domain, range(seeds))]
    summary = summarize(rows)
    sizes = {domain: size(domain) for domain in domains}
    times = {domain: decision_time(domain) for domain in domains}
    out: list[str] = []

    out += ["## Daño que queda con cada defensa", "",
            "Porcentaje de episodios en los que un secreto llegó a quien no debía o se movió dinero sin permiso. "
            "Menos es mejor.", "",
            "| Dominio | Tipo de episodio | Sin defensa | Filtro de coincidencia exacta | Quórum |",
            "|---|---|---|---|---|"]
    labels = {"attack": "Ataque repartido (k = 1, 2, 3)",
              "disguised": "El mismo ataque con el dato escrito en palabras",
              "injection": "Inyección en un documento, agentes honestos"}
    for domain in domains:
        kinds = importlib.import_module(f"quorum.scenarios.{domain}").KINDS
        for name, label in labels.items():
            cell = summary[domain].get(name)
            if cell:
                if name == "attack" and "wrong_recipient" in kinds:
                    label += " y envío al destinatario equivocado"
                out.append(f"| {DOMAINS[domain]} | {label} | {_pct(cell.harm_none, cell.n)} | "
                           f"{_pct(cell.harm_exact, cell.n)} | {_pct(cell.harm_quorum, cell.n)} |")

    out += ["", "## Trabajo legítimo que sobrevive", "",
            "Porcentaje de episodios honestos que terminan bien. Más es mejor. El trámite descuidado es un agente "
            "honesto que mira un dato restringido que no necesitaba: no filtra nada y aun así la compuerta lo detiene. "
            "Es el costo de la defensa y se reporta aparte.", "",
            "| Dominio | Trámite honesto, sin defensa | Trámite honesto, con Quórum | Trámite descuidado, con Quórum |",
            "|---|---|---|---|"]
    for domain in domains:
        honest, careless = summary[domain].get("honest"), summary[domain].get("careless")
        out.append(f"| {DOMAINS[domain]} | {_pct(honest.useful_none, honest.n)} | "
                   f"{_pct(honest.useful_quorum, honest.n)} | "
                   + (_pct(careless.useful_quorum, careless.n) if careless else "n/a") + " |")

    out += ["", "## La tabla de lo sensible, por dominio", "",
            "Es lo único que cambia de un dominio a otro. La escribe quien usa el sistema, en el `policy.toml` "
            "del dominio, y la compuerta la aplica sin interpretarla.", "",
            "| Dominio | Nace restringido | Lo escriben terceros | Salidas y qué puede llevar cada una | "
            "Cálculos autorizados sobre datos restringidos | Un tercero no ordena salidas |",
            "|---|---|---|---|---|---|"]
    for domain in domains:
        policy = importlib.import_module(f"quorum.scenarios.{domain}").POLICY
        code = lambda items: ", ".join(f"`{item}`" for item in items) or "ninguno"  # noqa: E731
        sinks = "; ".join(f"`{sink}`: {code(accepts) if accepts else 'nada restringido'}"
                          for sink, accepts in policy.sinks.items())
        out.append(f"| {DOMAINS[domain]} | {code(policy.restricted)} | {code(policy.untrusted)} | {sinks} | "
                   f"{code(sorted(policy.declassifiers))} | {'sí' if policy.strict_mode else 'no'} |")

    out += ["", "## Lo que cuesta llevar la compuerta a un dominio nuevo", "",
            "| Dominio | Líneas de política | Líneas de herramientas | Líneas cambiadas en el núcleo | "
            "Tiempo de una decisión |", "|---|---|---|---|---|"]
    for domain in domains:
        out.append(f"| {DOMAINS[domain]} | {sizes[domain]['policy']} | {sizes[domain]['tools']} | 0 | "
                   f"{_dec(times[domain])} µs |")
    out += ["", "El tiempo es la mediana de una decisión de la compuerta en esta máquina "
            "y cambia un poco entre corridas."]

    totals = Row("*", "*", "*")
    for domain in domains:
        for name in ("attack", "disguised", "injection"):
            cell = summary[domain].get(name)
            if cell:
                for field in ("n", "harm_none", "harm_exact", "harm_quorum"):
                    setattr(totals, field, getattr(totals, field) + getattr(cell, field))
    honest_n = sum(summary[d]["honest"].n for d in domains)
    honest_ok = sum(summary[d]["honest"].useful_quorum for d in domains)
    careless_n = sum(summary[d]["careless"].n for d in domains if "careless" in summary[d])
    careless_ok = sum(summary[d]["careless"].useful_quorum for d in domains if "careless" in summary[d])
    out += ["", "## En una frase", "",
            f"En {len(domains)} dominios y {totals.n} episodios adversos, el daño ocurre en "
            f"{_pct(totals.harm_none, totals.n)} sin defensa, en {_pct(totals.harm_exact, totals.n)} con el filtro de "
            f"coincidencia exacta y en {_pct(totals.harm_quorum, totals.n)} con Quórum. "
            f"De {honest_n} trámites honestos, Quórum deja terminar {_pct(honest_ok, honest_n)}. "
            f"El costo: de {careless_n} trámites descuidados, que no filtran nada, deja terminar "
            f"{_pct(careless_ok, careless_n)}. "
            "Son episodios guionados: miden el mecanismo, no la conducta de un modelo."]

    data = {"seeds": seeds, "domains": domains, "rows": [row.__dict__ for row in rows], "sizes": sizes,
            "decision_time_us": times}
    return "\n".join(out) + "\n", data


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m quorum.bench", description=__doc__.split("\n\n")[0])
    parser.add_argument("--seeds", type=int, default=200, help="episodes per kind (default 200)")
    parser.add_argument("--domains", nargs="*", default=list(DOMAINS), choices=list(DOMAINS))
    parser.add_argument("--out", default="", help="write the tables into this Markdown file, between its markers")
    parser.add_argument("--json", default="", help="also save every count as JSON")
    args = parser.parse_args(argv)

    tables, data = report(args.domains, args.seeds)
    if args.json:
        Path(args.json).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not args.out:
        sys.stdout.write(tables)
        return
    path, start, end = Path(args.out), "<!-- bench:start -->", "<!-- bench:end -->"
    text = path.read_text(encoding="utf-8")
    if start not in text or end not in text:
        sys.exit(f"{path} has no {start} ... {end} markers")
    head, rest = text.split(start, 1)
    path.write_text(f"{head}{start}\n\n{tables}\n{end}{rest.split(end, 1)[1]}", encoding="utf-8")
    print(f"tables written to {path} ({args.seeds} seeds per kind, {len(args.domains)} domains)")


if __name__ == "__main__":
    main()
