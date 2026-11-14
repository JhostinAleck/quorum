"""Attacks on the gate: provenance stops every route through a restricted read, not the public scores."""
from quorum.eval.break_gate import table


def test_every_attempt_through_a_restricted_read_is_blocked_and_the_scores_still_leak():
    t = table(seeds=range(4))
    for name in ("copia exacta (k=1)", "en letras, dígito a dígito", "en millones, redondeado",
                 "partido entre dos agentes"):
        n, control, blocked, exact, info = t[name]
        assert control == n, f"{name}: the control must carry the amount"
        assert blocked == n and exact == 0 and info == 0
    n, control, blocked, exact, info = t["invertir los puntajes públicos"]
    assert blocked == 0 and exact == 0 and info == n      # known hole: declassified scores
