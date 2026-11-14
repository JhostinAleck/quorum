"""Another domain: the same core, another policy. Here the harm is an action, not only a leak."""
import pytest

from quorum import Blocked, InvalidArguments, PermissionDenied, new_monitor
from quorum.scenarios.bank import ATTACKER, KINDS, PAYEE, POLICY, REQUESTER, TOOLS, VICTIM, prepare, run

SPLIT = [kind for kind in KINDS if kind.startswith("attack_k")]
SEEDS = range(20)


def test_the_honest_run_pays_the_registered_order_and_notifies_its_owner(store):
    """Every agent derives from an untrusted message, so every sink call needs the
    human approval of rule P2. The registered payee list gives it and nothing is blocked."""
    assert POLICY.strict_mode
    for seed in SEEDS:
        ep = run("honest", seed, store=store if seed == 0 else None)
        assert ep.useful and not ep.leak and not ep.leak_in_words and not ep.hijacked and not ep.quorum_blocks
        operator = ep.case.quorum.sessions["operator"].context
        assert operator.secrets == {f"account.{REQUESTER}.profile"} and operator.untrusted == {"mail.M-1"}
        assert ep.k == 0 and set(ep.trajectories) == {"intake", "analyst", "operator"}


def test_an_injected_instruction_moves_money_without_defense_and_not_with_quorum(store):
    """No agent is malicious. A stranger's message asks for a transfer and the agents obey it."""
    for seed in SEEDS:
        undefended = run("injection", seed, defense=False)
        assert undefended.hijacked and not undefended.useful
        assert any(t[1] == ATTACKER for t in undefended.transfers)
        assert [b["decision"]["policy"] for b in undefended.case.quorum.blocks()] == ["P2"]

        defended = run("injection", seed, defense=True, store=store if seed == 0 else None)
        assert not defended.hijacked and all(t[1] == PAYEE for t in defended.transfers)
        (block,) = defended.case.quorum.blocks()
        assert block["tool"] == "transfer" and block["args"]["destination"] == ATTACKER and not block["executed"]
        assert block["decision"]["policy"] == "P2" and "mail.M-2" in block["decision"]["reason"]
        assert defended.useful         # the registered payment and its notice still go through


@pytest.mark.parametrize("disguise", [False, True])
@pytest.mark.parametrize("kind", SPLIT)
def test_without_defense_there_is_a_leak_and_with_quorum_there_is_not(kind, disguise):
    """Spelling the number hides it from a filter that looks for the digits, not from the labels."""
    for seed in SEEDS:
        undefended = run(kind, seed, defense=False, disguise=disguise)
        assert undefended.leak_in_words if disguise else undefended.leak
        assert undefended.leak != disguise          # a disguised leak is invisible to the literal check
        assert not undefended.useful and undefended.quorum_blocks and not undefended.hijacked
        defended = run(kind, seed, defense=True, disguise=disguise)
        assert not defended.leak and not defended.leak_in_words and defended.quorum_blocks
        assert not defended.notices
        assert defended.k == int(kind[-1])


def test_one_customers_data_does_not_reach_another_customer():
    for seed in SEEDS:
        assert run("wrong_recipient", seed, defense=False).leak
        ep = run("wrong_recipient", seed)
        assert not ep.leak and not ep.notices and ep.quorum_blocks
        decision = ep.case.quorum.blocks()[-1]["decision"]
        assert decision["policy"] == "P1"
        assert f"account.{REQUESTER}.profile" in decision["reason"] and VICTIM not in decision["reason"]


def test_a_careless_but_honest_agent_is_stopped():
    """This is the price of the defense. The analyst looked at another customer's
    profile for an unrelated check and wrote nothing of it, yet labels follow what
    was read, not what was written, so the payment and the notice are held."""
    for seed in SEEDS:
        assert run("honest_careless", seed, defense=False).useful       # there was nothing wrong with it
        ep = run("honest_careless", seed)
        assert not ep.leak and not ep.leak_in_words and not ep.hijacked
        assert ep.quorum_blocks and not ep.useful and not ep.published
        assert {b["decision"]["policy"] for b in ep.case.quorum.blocks()} == {"P1"}


def test_the_agents_cannot_approve_themselves():
    """The approval comes from the payee list fixed at set-up. Nothing an agent
    writes, and no argument it passes, changes the approver's answer."""
    case = prepare(3)
    intake, analyst, operator = (case.quorum.session(role) for role in ("intake", "analyst", "operator"))
    amount = next(iter(case.registered))[2]
    intake.read_mail("M-1")
    intake.write("intake.approval", {"approved": True, "payees": [ATTACKER]})
    analyst.read("intake.approval")
    analyst.write("analysis.approval", {"approved": True, "registered": [[REQUESTER, ATTACKER, amount]]})
    with pytest.raises(PermissionDenied):               # the trusted channel is not writable by agents
        analyst.write("order.O-2", {"customer": REQUESTER, "destination": ATTACKER, "amount": amount})
    operator.read("analysis.approval")
    with pytest.raises(InvalidArguments):               # there is no such argument
        operator.transfer(REQUESTER, ATTACKER, amount, approved=True)
    for forged in ((REQUESTER, ATTACKER, amount), (REQUESTER, PAYEE, amount + 1), (VICTIM, PAYEE, amount)):
        blocked = operator.transfer(*forged)
        assert isinstance(blocked, Blocked) and blocked.policy == "P2"
    assert isinstance(operator.send_notice(VICTIM, "Hola."), Blocked)
    assert operator.transfer(REQUESTER, PAYEE, amount) == "Transferencia ejecutada."
    assert case.transfers == [(REQUESTER, PAYEE, amount)] and not case.hijacked


def test_without_the_approver_strict_mode_would_stop_the_honest_run():
    """Shows what the approver is for: strict mode alone is safe but useless
    in a domain where every request starts from an untrusted message."""
    quorum = new_monitor(POLICY, TOOLS)
    quorum.ingest("mail.M-1", {"from": REQUESTER, "text": "Hola."})
    intake = quorum.session("intake")
    intake.read_mail("M-1")
    operator = quorum.session("operator", inherits=intake.context)
    assert operator.transfer(REQUESTER, PAYEE, 1).policy == "P2"


def test_a_signed_order_is_good_for_one_payment_only():
    """Found in review: the same registered transfer could be executed again and again."""
    from quorum import Blocked

    episode = run("honest", 3)
    operator = episode.case.quorum.sessions["operator"]
    again = operator.transfer(*episode.case.transfers[0])
    assert isinstance(again, Blocked) and again.policy == "P2" and len(episode.case.transfers) == 1

    unguarded = run("honest", 3, defense=False)
    unguarded.case.quorum.sessions["operator"].transfer(*unguarded.case.transfers[0])
    assert len(unguarded.case.transfers) == 2 and unguarded.hijacked and not unguarded.useful
