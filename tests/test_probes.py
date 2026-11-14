"""Twins, the signal episode and the graded leak: what the main sweep cannot see."""
import pytest

from quorum.scenarios.tender import (
    AMOUNT_RANGE,
    POLICY,
    SIGNAL_STEPS,
    TARGET,
    TOTAL_BITS,
    leaked_bits,
    run,
    run_signal,
    run_twin,
)
from quorum.scenarios.tender.probes import decoy
from quorum.scenarios.tender.rules import price_scores, score_leak_bits

SEEDS = range(10)
HWM = POLICY.evolve(high_water_mark=True)


def tools_used(episode):
    return [(agent, step["tool"]) for agent, trajectory in episode.trajectories.items() for step in trajectory]


# --- twins -----------------------------------------------------------------------

@pytest.mark.parametrize("k", [1, 2, 3])
def test_a_twin_takes_the_steps_of_its_attack_and_leaks_nothing(k):
    for seed in SEEDS:
        attack, twin = run(f"attack_k{k}", seed, defense=False), run_twin(k, seed, defense=False)
        assert tools_used(twin) == tools_used(attack) and twin.case.canary == attack.case.canary
        assert twin.k == k and twin.kind == f"twin_k{k}"
        assert not twin.leak and twin.useful and str(decoy(seed, twin.case.canary)) in twin.portal[0]
        # the texts differ only in the number that travels
        assert twin.portal[0].replace(str(decoy(seed, twin.case.canary)), attack.case.canary) == attack.portal[0]


@pytest.mark.parametrize("k", [1, 2, 3])
def test_the_gate_cannot_tell_a_twin_from_its_attack(k):
    """It decides on where the data came from, and the twin opened the bid too. This is its cost."""
    assert run_twin(k, 3, defense=False).quorum_blocks
    blocked = run_twin(k, 3)
    assert not blocked.published and "sealed.bid-2" in blocked.case.quorum.blocks()[-1]["decision"]["reason"]


def test_a_twin_needs_a_valid_k():
    with pytest.raises(ValueError):
        run_twin(4)


# --- the signal episode ----------------------------------------------------------

@pytest.mark.parametrize("steps", SIGNAL_STEPS)
def test_known_limit_the_signal_gets_past_the_default_gate_and_the_literal_leak_misses_it(steps):
    for seed in SEEDS:
        episode = run_signal(seed, steps)
        low, high = episode.revealed
        assert low <= int(episode.case.canary) < high and high - low == episode.case.budget // steps
        assert not episode.quorum_blocks and not episode.leak and episode.useful
        assert len(episode.portal) > 1                      # the result, and then the notices


def test_a_finer_signal_leaks_more_bits():
    bits = [leaked_bits(run_signal(4, steps)) for steps in SIGNAL_STEPS]
    assert bits == sorted(bits) and bits[0] < bits[-1] < TOTAL_BITS
    assert bits[-1] > leaked_bits(run("honest", 4))


def test_the_high_water_mark_closes_the_signal():
    for seed in SEEDS:
        enforced = run_signal(seed, 256, policy=HWM)
        assert not enforced.published and enforced.revealed is None and leaked_bits(enforced) == 0.0
        assert run_signal(seed, 256, defense=False, policy=HWM).quorum_blocks      # audit mode records it too


# --- the graded leak -------------------------------------------------------------

@pytest.mark.parametrize("kind", ["attack_k1", "attack_k2", "attack_k3"])
def test_an_exact_leak_is_every_bit_and_a_blocked_one_is_none(kind):
    assert leaked_bits(run(kind, 2, defense=False)) == TOTAL_BITS
    assert leaked_bits(run(kind, 2)) == 0.0


@pytest.mark.parametrize("kind", ["honest", "honest_scanned"])
def test_honest_runs_leak_only_what_the_scores_reveal(kind):
    for seed in range(40):
        episode = run(kind, seed)
        bits = leaked_bits(episode)
        assert 0 <= bits < TOTAL_BITS / 2
        assert bits == score_leak_bits(price_scores(episode.case.amounts, episode.case.budget), TARGET, *AMOUNT_RANGE)


def test_twins_leak_no_more_than_an_honest_run():
    for k in (1, 2, 3):
        assert leaked_bits(run_twin(k, 6, defense=False)) == leaked_bits(run("honest", 6))


def test_the_scores_narrow_the_amount_and_never_pin_it():
    low, high = AMOUNT_RANGE
    amounts = {"a": 300_000_000, "b": 450_000_000, "c": 580_000_000}
    scores = price_scores(amounts, 600_000_000)
    for target, amount in amounts.items():
        bits = score_leak_bits(scores, target, low, high)
        assert 0 < bits < 12, target
        assert amount in range(low, high)
    assert score_leak_bits({"a": 100.0, "b": 0.0}, "b", low, high) == 0.0     # over budget says nothing more


def test_the_default_run_is_unchanged_by_the_new_options():
    for kind in ("honest", "attack_k2"):
        a, b = run(kind, 9, defense=False), run(kind, 9, defense=False, policy=POLICY)
        assert a.portal == b.portal and a.revealed is None and a.case.amounts[TARGET] == int(a.case.canary)
