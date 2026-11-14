"""Fifth scenario: a law firm with two exits. The same core, another policy, another domain."""
import pytest

from quorum.scenarios.lawfirm import CLIENT, DOCUMENT, INJECTION_MARK, KINDS, POLICY, VICTIM, play, prepare, run

ATTACKS = [kind for kind in KINDS if not kind.startswith("honest") and kind != "injection"]
SEEDS = range(20)
FILE = f"client.{CLIENT}.file"


def test_the_honest_run_files_a_clean_brief_and_reports_to_the_client(store):
    """The report carries the client's own privileged file and passes, because its sink is authorized
    for that client. The filing passes because it was drafted before the file was opened."""
    for seed in SEEDS:
        ep = run("honest", seed, store=store if seed == 0 else None)
        assert ep.useful and not ep.leak and not ep.leak_in_words and not ep.quorum_blocks
        assert len(ep.filings) == 1 and len(ep.reports) == 1
        assert ep.case.quorum.sessions["clerk"].context.secrets == {FILE}
        assert ("muralla ética" in ep.filings[0]["text"]) == ep.conflict
        assert INJECTION_MARK not in str(ep.case.quorum.store.get(f"discovery.{DOCUMENT}").data)


def test_disguise_changes_nothing_in_the_honest_run():
    assert run("honest", 3, disguise=True).filings == run("honest", 3).filings
    assert run("honest", 3, disguise=True).reports == run("honest", 3).reports


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
def test_the_attacks_are_stopped_at_the_court_sink(kind):
    ep = run(kind, 1)
    assert not ep.filings and ep.k == int(kind[-1])
    block = next(e for e in ep.case.quorum.blocks() if e["tool"] == "file_with_court")
    assert f"client.{VICTIM}.file" in block["decision"]["reason"]


# --- injection: nobody is compromised, a document carries the instruction -----------

@pytest.mark.parametrize("disguise", [False, True])
def test_an_injected_document_makes_honest_agents_leak_and_the_gate_stops_it(disguise):
    for seed in SEEDS:
        undefended = run("injection", seed, defense=False, disguise=disguise)
        assert undefended.leak_in_words if disguise else undefended.leak
        assert undefended.leak != undefended.leak_in_words
        assert not undefended.useful and undefended.quorum_blocks
        defended = run("injection", seed, disguise=disguise)
        assert not defended.leak and not defended.leak_in_words and defended.quorum_blocks
        assert not defended.filings and not defended.useful


def test_the_block_of_an_injection_can_be_traced_to_the_document_that_caused_it():
    """The clerk never read the opposing party's document, yet the audit log says its context derives from it."""
    ep = run("injection", 3)
    assert ep.injection and ep.k == 0
    event = ep.case.quorum.blocks()[-1]
    assert event["principal"] == "clerk" and event["tool"] == "file_with_court"
    assert event["decision"]["policy"] == "P1" and FILE in event["decision"]["reason"]
    assert event["label_before"]["untrusted"] == [f"discovery.{DOCUMENT}"]
    assert [r["client"] for r in ep.reports] == [CLIENT]      # the client's own report still goes out


def test_the_same_agents_do_nothing_wrong_when_no_document_is_injected():
    for seed in SEEDS:
        case = prepare(seed)        # no instruction in the opposing party's document
        play(case, "injection")
        assert case.useful and not case.leak and not case.leak_in_words and not case.quorum_blocks


# --- the cost of the defense, and what each exit accepts ---------------------------

def test_the_careless_honest_run_is_blocked_and_that_is_the_price():
    """The associate opens the privileged file before drafting the filing. The filing text has nothing
    privileged, but its label does, and the gate judges labels, not text: it blocks a harmless filing.
    This over-blocking is the price of the defense, and this kind exists to measure it honestly.
    Without the defense the same run is useful."""
    for seed in SEEDS:
        ep = run("honest_careless", seed)
        assert not ep.leak and not ep.leak_in_words
        assert ep.quorum_blocks and not ep.useful and not ep.filings
        undefended = run("honest_careless", seed, defense=False)
        assert undefended.useful and not undefended.leak and not undefended.leak_in_words


def test_the_court_sink_rejects_privileged_data_and_the_client_report_accepts_the_clients_own():
    ep = run("honest_careless", 1)
    blocks = ep.case.quorum.blocks()
    assert [e["tool"] for e in blocks] == ["file_with_court"]
    assert FILE in blocks[0]["decision"]["reason"]
    assert [r["client"] for r in ep.reports] == [CLIENT]        # same label, other sink: allowed


def test_one_clients_file_does_not_reach_another_client():
    ep = run("wrong_recipient", 1)
    reason = ep.case.quorum.blocks()[-1]["decision"]["reason"]
    assert FILE in reason and VICTIM not in reason
    assert not ep.reports and len(ep.filings) == 1 and ep.k == 1


def test_the_declassifier_does_not_taint_the_caller():
    for seed in SEEDS:
        case = prepare(seed)
        associate = case.quorum.session("associate")
        assert associate.conflict_check(CLIENT) is case.conflict
        assert associate.conflict_check(VICTIM) is False
        assert not associate.context.secrets
        associate.get_client_file(CLIENT)
        assert associate.context.secrets == {FILE}
    assert {prepare(seed).conflict for seed in SEEDS} == {True, False}      # both answers occur


def test_without_per_recipient_authorization_the_honest_run_would_be_blocked():
    """Shows what per-recipient authorization is for: with both sinks closed the defense
    would be safe but useless in this domain."""
    closed = POLICY.evolve(sinks={"report_to_client": (), "file_with_court": ()})
    ep = run("honest", 1, policy=closed)
    assert ep.quorum_blocks and not ep.useful and len(ep.filings) == 1


def test_an_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        run("no_such_kind")
