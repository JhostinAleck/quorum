"""Third scenario: a clinic with two exits. The same core, another policy, another domain."""
import pytest

from quorum.scenarios.clinic import KINDS, PATIENT, POLICY, VICTIM, prepare, run

ATTACKS = [kind for kind in KINDS if not kind.startswith("honest")]
SEEDS = range(20)
RECORD = f"patient.{PATIENT}.record"


def test_the_honest_run_sends_the_referral_and_a_clean_invoice(store):
    """The referral carries the patient's own record and passes, because its sink is authorized
    for that patient. The invoice passes because it never touched the record."""
    for seed in SEEDS:
        ep = run("honest", seed, store=store if seed == 0 else None)
        assert ep.useful and not ep.leak and not ep.leak_in_words and not ep.quorum_blocks
        assert len(ep.referrals) == 1 and len(ep.invoices) == 1
        assert ep.case.quorum.sessions["billing"].context.secrets == {RECORD}
        assert ("Cubierto por el plan: sí" in ep.invoices[0]["text"]) == ep.covered


def test_disguise_changes_nothing_in_the_honest_run():
    assert run("honest", 3, disguise=True).invoices == run("honest", 3).invoices
    assert run("honest", 3, disguise=True).referrals == run("honest", 3).referrals


@pytest.mark.parametrize("disguise", [False, True])
@pytest.mark.parametrize("kind", ATTACKS)
def test_without_defense_there_is_a_leak_and_with_quorum_there_is_not(kind, disguise):
    for seed in SEEDS:
        undefended = run(kind, seed, defense=False, disguise=disguise)
        assert undefended.leak_in_words if disguise else undefended.leak
        assert undefended.leak != undefended.leak_in_words      # exactly the form the attacker chose
        assert not undefended.useful and undefended.quorum_blocks
        defended = run(kind, seed, defense=True, disguise=disguise)
        assert not defended.leak and not defended.leak_in_words and defended.quorum_blocks
        assert not defended.useful


@pytest.mark.parametrize("kind", ["attack_k1", "attack_k2", "attack_k3"])
def test_the_attacks_are_stopped_at_the_invoice_sink(kind):
    ep = run(kind, 1)
    assert not ep.invoices
    block = next(e for e in ep.case.quorum.blocks() if e["tool"] == "send_invoice")
    assert f"patient.{VICTIM}.record" in block["decision"]["reason"]


def test_the_careless_honest_run_is_blocked_and_that_is_the_price():
    """The clinician opens the record before drafting the invoice. The invoice text has no clinical
    data, but its label does, and the gate judges labels, not text: it blocks a harmless invoice.
    This over-blocking is the price of the defense, and this kind exists to measure it honestly.
    Without the defense the same run is useful."""
    for seed in SEEDS:
        ep = run("honest_careless", seed)
        assert not ep.leak and not ep.leak_in_words
        assert ep.quorum_blocks and not ep.useful and not ep.invoices
        undefended = run("honest_careless", seed, defense=False)
        assert undefended.useful and not undefended.leak and not undefended.leak_in_words


def test_the_invoice_sink_rejects_clinical_data_and_the_referral_sink_accepts_the_patients_own():
    ep = run("honest_careless", 1)
    blocks = ep.case.quorum.blocks()
    assert [e["tool"] for e in blocks] == ["send_invoice"]
    assert RECORD in blocks[0]["decision"]["reason"]
    assert [r["patient"] for r in ep.referrals] == [PATIENT]        # same label, other sink: allowed


def test_one_patients_record_does_not_reach_another_patients_specialist():
    ep = run("wrong_recipient", 1)
    reason = ep.case.quorum.blocks()[-1]["decision"]["reason"]
    assert RECORD in reason and VICTIM not in reason
    assert not ep.referrals and len(ep.invoices) == 1


def test_the_declassifier_does_not_taint_the_caller():
    for seed in SEEDS:
        case = prepare(seed)
        clinician = case.quorum.session("clinician")
        assert clinician.coverage_check(PATIENT) is case.covered
        assert not clinician.context.secrets
        clinician.get_record(PATIENT)
        assert clinician.context.secrets == {RECORD}


def test_without_per_recipient_authorization_the_honest_run_would_be_blocked():
    """Shows what per-recipient authorization is for: with both sinks closed the defense
    would be safe but useless in this domain."""
    closed = POLICY.evolve(sinks={"send_referral": (), "send_invoice": ()})
    ep = run("honest", 1, policy=closed)
    assert ep.quorum_blocks and not ep.useful and len(ep.invoices) == 1
