"""Second scenario: the same core, another policy, another domain."""
import pytest

from quorum.scenarios.helpdesk import KINDS, POLICY, REQUESTER, VICTIM, run

ATTACKS = [kind for kind in KINDS if kind != "honest"]
SEEDS = range(20)


def test_the_honest_run_replies_with_the_citizens_own_data(store):
    """The reply carries restricted data of whoever asks and still passes,
    because the sink is authorized for its recipient."""
    for seed in SEEDS:
        ep = run("honest", seed, store=store if seed == 0 else None)
        assert ep.useful and not ep.leak and not ep.quorum_blocks
        assert ep.case.quorum.sessions["writer"].context.secrets == {
            f"citizen.{REQUESTER}.record", f"citizen.{REQUESTER}.status"}


@pytest.mark.parametrize("kind", ATTACKS)
def test_without_defense_there_is_a_leak_and_with_quorum_there_is_not(kind):
    for seed in SEEDS:
        undefended = run(kind, seed, defense=False)
        assert undefended.leak and not undefended.useful and undefended.quorum_blocks
        defended = run(kind, seed, defense=True)
        assert not defended.leak and not defended.published and defended.quorum_blocks


def test_one_persons_data_does_not_reach_another_person():
    ep = run("wrong_recipient", 1)
    reason = ep.case.quorum.blocks()[-1]["decision"]["reason"]
    assert f"citizen.{REQUESTER}.record" in reason and VICTIM not in reason


def test_without_per_recipient_authorization_the_honest_run_would_be_blocked():
    """Shows what per-recipient authorization is for: without it, the defense
    would be safe but useless in this domain."""
    closed = POLICY.evolve(sinks={"reply": ()})
    assert run("honest", 1, policy=closed).quorum_blocks
