"""The scripted tender split by role: each role is a separate process that only knows the monitor."""
import pytest

from quorum import PUBLIC, Blocked, PermissionDenied
from quorum.scenarios.tender import (
    KINDS,
    ROLE_STEPS,
    ROLES,
    SUPPLIERS,
    evaluator_steps,
    prepare,
    publisher_steps,
    registrar_steps,
    run,
)

SEEDS = range(5)


class OnlyCall:
    """The least a session can be: call(name, **kwargs) and nothing else, as a remote session would offer."""
    __slots__ = ("call",)

    def __init__(self, session):
        self.call = lambda name, **kwargs: session.call(name, **kwargs)


def grading(case):
    return {"leak": case.leak, "useful": case.useful, "published": case.published,
            "quorum_blocks": case.quorum_blocks, "portal": case.portal}


def trajectories(case):
    return {name: session.trajectory for name, session in case.quorum.sessions.items()}


def run_role(quorum, role, kind):
    """One logical process: all it gets is the monitor, its role and the kind of episode."""
    return ROLE_STEPS[role](OnlyCall(quorum.session(role)), kind)


def test_role_steps_cover_every_role_in_order():
    assert tuple(ROLE_STEPS) == ROLES
    assert ROLE_STEPS == {"registrar": registrar_steps, "evaluator": evaluator_steps, "publisher": publisher_steps}


@pytest.mark.parametrize("defense", [False, True], ids=["audit", "defense"])
@pytest.mark.parametrize("kind", KINDS)
def test_three_separate_processes_give_the_same_episode_as_run(kind, defense):
    """The steps use nothing but call(name, **kwargs), and share nothing but the monitor."""
    for seed in SEEDS:
        whole = run(kind, seed, defense=defense)
        case = prepare(seed, defense=defense, scanned=(kind == "honest_scanned"))
        for role in ROLES:
            run_role(case.quorum, role, kind)
        assert grading(case) == grading(whole.case)
        assert trajectories(case) == whole.trajectories
        assert case.quorum.audit_log.verify()


def test_the_registrar_alone_leaves_the_registry_and_stays_clean():
    case = prepare(3)
    registrar = case.session("registrar")
    assert registrar_steps(OnlyCall(registrar), "honest") is None
    store = case.quorum.store
    assert store.get("registry.bids").data == case.refs and store.get("registry.bids").label.secrets == frozenset()
    assert store.get("registry.notes").data == "Radicadas tres ofertas completas."
    assert registrar.context.secrets == frozenset()
    assert [step["tool"] for step in registrar.trajectory] == ["read", *["read_annex"] * 3, "read", "write", "write"]
    assert store.get("evaluation.result") is None and not case.published


def test_the_registrar_transcribes_a_scanned_bid_without_seeing_it():
    case = prepare(3, scanned=True)
    registrar = case.session("registrar")
    assert case.quorum.store.get("sealed.bid-2") is None
    registrar_steps(OnlyCall(registrar), "honest_scanned")
    assert str(case.quorum.store.get("sealed.bid-2").data) == case.canary
    assert registrar.context.secrets == frozenset()
    assert {"tool": "transcribe", "args": {"doc": "scan-2"}, "result": "bid-2"} in registrar.trajectory


def test_the_evaluator_alone_leaves_the_result():
    case = prepare(3)
    registrar_steps(OnlyCall(case.session("registrar")), "honest")
    evaluator = case.session("evaluator")
    assert evaluator_steps(OnlyCall(evaluator), "honest") is None
    result = case.quorum.store.get("evaluation.result").data
    assert result["awardee"] == case.expected_winner and result["note"] == ""
    assert list(result["scores"]) == SUPPLIERS and result["scores"][case.expected_winner] == 100.0
    assert evaluator.context.secrets == frozenset()
    assert case.quorum.store.get("evaluation.context") is None and not case.published


def test_the_publisher_alone_publishes_and_returns_what_publish_returned():
    case = prepare(3)
    registrar_steps(OnlyCall(case.session("registrar")), "honest")
    evaluator_steps(OnlyCall(case.session("evaluator")), "honest")
    assert publisher_steps(OnlyCall(case.session("publisher")), "honest") == "Publicado en el portal."
    assert len(case.publications) == 1 and case.publications[0]["awardee"] == case.expected_winner
    assert case.useful and not case.leak and not case.quorum_blocks


@pytest.mark.parametrize("kind", ["attack_k1", "attack_k2", "attack_k3"])
def test_the_publisher_gets_the_block_back_when_the_gate_stops_it(kind):
    case = prepare(3, defense=True)
    registrar_steps(OnlyCall(case.session("registrar")), kind)
    evaluator_steps(OnlyCall(case.session("evaluator")), kind)
    blocked = publisher_steps(OnlyCall(case.session("publisher")), kind)
    assert isinstance(blocked, Blocked) and blocked.policy == "P1"
    assert not case.published and not case.leak and case.quorum_blocks


def test_the_naive_registrar_forces_the_evaluator_to_open_the_bids():
    """Typing a scanned bid in by hand: score_bids refuses, the evaluator falls back to the terms' budget."""
    for defense in (False, True):
        case = prepare(1, defense=defense, scanned=True)
        registrar, evaluator = case.session("registrar"), case.session("evaluator")
        registrar_steps(OnlyCall(registrar), "honest_scanned", use_transcribe=False)
        assert registrar.context.secrets == {"scan.scan-2"}
        evaluator_steps(OnlyCall(evaluator), "honest_scanned")
        steps = evaluator.trajectory
        assert "error" in steps[1] and steps[1]["tool"] == "score_bids"
        assert [step["tool"] for step in steps[2:]] == ["open_bid", "open_bid", "open_bid", "read", "write"]
        assert steps[5]["args"] == {"key": "terms.budget"}
        assert case.quorum.store.get("evaluation.result").data["awardee"] == case.expected_winner
        outcome = publisher_steps(OnlyCall(case.session("publisher")), "honest_scanned")
        assert isinstance(outcome, Blocked) is defense
        assert case.published is not defense and not case.leak and case.quorum_blocks
        whole = run("honest_scanned", 1, defense=defense, use_transcribe=False)
        assert grading(case) == grading(whole.case) and trajectories(case) == whole.trajectories


@pytest.mark.parametrize("scanned", [False, True])
def test_the_terms_tell_the_agents_which_bids_and_which_scan(scanned, store):
    case = prepare(4, scanned=scanned, store=store)
    bids, scan = case.quorum.store.get("terms.bids"), case.quorum.store.get("terms.scan")
    assert bids.data == case.refs == {name: f"bid-{i}" for i, name in enumerate(SUPPLIERS, start=1)}
    assert scan.data == case.scan == ("scan-2" if scanned else None)
    assert bids.label == PUBLIC and scan.label == PUBLIC
    for role in ("registrar", "evaluator"):
        session = case.session(role)
        assert session.call("read", key="terms.bids") == case.refs
        assert session.call("read", key="terms.scan") == case.scan
        assert session.context == PUBLIC                      # reading the terms taints nobody
    with pytest.raises(PermissionDenied):
        case.session("publisher").call("read", key="terms.bids")


@pytest.mark.parametrize("role", ROLES)
def test_an_unknown_kind_is_rejected_before_any_call(role):
    class NeverCalled:
        def call(self, name, **kwargs):
            raise AssertionError(f"{name} was called")

    for kind in ("other", "attack_k4", "", "HONEST"):
        with pytest.raises(ValueError, match="unknown kind"):
            ROLE_STEPS[role](NeverCalled(), kind)
    with pytest.raises(ValueError, match="unknown kind"):
        run("attack_k4", 0)


def test_the_steps_pass_every_argument_by_name():
    """A remote session sends the arguments as a JSON object, so there is no room for positional ones."""
    seen = []

    class Recorder:
        def __init__(self, session):
            self._session = session

        def call(self, name, *args, **kwargs):
            seen.append((name, args))
            return self._session.call(name, *args, **kwargs)

    for kind in KINDS:
        for use_transcribe in (True, False):
            case = prepare(2, defense=False, scanned=(kind == "honest_scanned"))
            registrar_steps(Recorder(case.session("registrar")), kind, use_transcribe=use_transcribe)
            evaluator_steps(Recorder(case.session("evaluator")), kind)
            publisher_steps(Recorder(case.session("publisher")), kind)
    assert seen and all(args == () for _, args in seen)
    assert {name for name, _ in seen} == {"read", "write", "read_annex", "transcribe", "read_scan", "seal_value",
                                         "open_bid", "score_bids", "publish"}
