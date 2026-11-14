"""Scripted sweep: one row per episode, in the CSV format of docs/tareas.md.

  uv run python -m analysis.sweep --out resultados/guionado.csv
  uv run --extra eval python -m analysis.metrics resultados/guionado.csv

Every episode runs once with the gate in audit mode, so nothing is blocked and every arm
is read off the same behaviour. It runs a second time with high_water_mark on, to get that
arm too (hwm_blocks).

Kinds: honest and honest_scanned, attack_k1..3, twin_k1..3 (the hard negative of each
attack, same seed) and attack_signal (the missing-keys channel, see probes.py).

No model is called. The columns m1_score and m2_score are not written: whoever runs the
monitors adds them to the CSV, reading the trajectories that --trajectories dumps, and
analysis.metrics picks up every column that ends in _score.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any

from quorum.scenarios.tender import POLICY, SIGNAL_STEPS, Episode, leaked_bits, run, run_signal, run_twin

COLUMNS = ["kind", "k", "seed", "steps", "leak", "leaked_bits", "quorum_blocks", "hwm_blocks", "useful", "error"]
HWM = POLICY.evolve(high_water_mark=True)


def episodes(honest: int, per_k: int, signal: int, scanned: float, seed: int) -> list[tuple[str, int, int | None]]:
    """(kind, seed, steps) of every episode. Attacks and their twins share seeds."""
    rng = random.Random(seed)
    plan: list[tuple[str, int, int | None]] = [
        ("honest_scanned" if rng.random() < scanned else "honest", i, None) for i in range(honest)]
    for prefix in ("attack", "twin"):
        plan += [(f"{prefix}_k{k}", i, None) for k in (1, 2, 3) for i in range(per_k)]
    plan += [("attack_signal", i, SIGNAL_STEPS[i % len(SIGNAL_STEPS)]) for i in range(signal)]
    return plan


def run_one(kind: str, seed: int, steps: int | None, *, hwm: bool = False) -> Episode:
    if kind == "attack_signal":
        return run_signal(seed, steps or SIGNAL_STEPS[0], defense=False, policy=HWM if hwm else POLICY)
    if kind.startswith("twin_k"):
        if hwm:   # a twin opens the bid like its attack, so the high-water mark sees the same thing
            return run(f"attack_k{kind[-1]}", seed, defense=False, policy=HWM)
        return run_twin(int(kind[-1]), seed, defense=False)
    return run(kind, seed, defense=False, policy=HWM if hwm else POLICY)


def row(kind: str, seed: int, steps: int | None) -> tuple[dict[str, Any], Episode]:
    episode = run_one(kind, seed, steps)
    return {"kind": kind, "k": episode.k, "seed": seed, "steps": steps or "", "leak": int(episode.leak),
            "leaked_bits": round(leaked_bits(episode), 2), "quorum_blocks": int(episode.quorum_blocks),
            "hwm_blocks": int(run_one(kind, seed, steps, hwm=True).quorum_blocks),
            "useful": int(episode.useful), "error": ""}, episode


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="resultados/guionado.csv")
    ap.add_argument("--trajectories",
                    help="also write what each agent did, one JSON line per episode, for the monitors")
    ap.add_argument("--honest", type=int, default=300)
    ap.add_argument("--per-k", type=int, default=60, help="attacks for each k, and as many twins")
    ap.add_argument("--signal", type=int, default=60)
    ap.add_argument("--scanned", type=float, default=0.5, help="fraction of the honest runs with a scanned bid")
    ap.add_argument("--seed", type=int, default=20261114)
    a = ap.parse_args()

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dump = open(a.trajectories, "w", encoding="utf-8") if a.trajectories else None
    try:
        with out.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            for kind, seed, steps in episodes(a.honest, a.per_k, a.signal, a.scanned, a.seed):
                data, episode = row(kind, seed, steps)
                writer.writerow(data)
                if dump:
                    dump.write(json.dumps({"kind": kind, "seed": seed, "trajectories": episode.trajectories,
                                           "portal": episode.portal}, ensure_ascii=False, default=str) + "\n")
    finally:
        if dump:
            dump.close()
    print(f"{out}: {a.honest} honest, {3 * a.per_k} attacks, {3 * a.per_k} twins, {a.signal} signal")


if __name__ == "__main__":
    main()
