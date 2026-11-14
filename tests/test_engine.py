"""The reference monitor, tested with an abstract scenario (tests/mini.py)."""
import threading

import pytest
from mini import POLICY, TOOLS, emit, new

from quorum.core import (
    PUBLIC,
    Blocked,
    Decision,
    InvalidArguments,
    InvalidConfiguration,
    Kind,
    PermissionDenied,
    Policy,
    Quorum,
    QuotaExceeded,
    ToolError,
    UnknownTool,
    restricted,
    tool,
    untrusted,
)

# --- propagation ----------------------------------------------------------------

def test_reading_taints_and_writing_inherits_across_agents(store):
    q = new(store=store)
    a, b = q.session("a", "agent"), q.session("b", "agent")
    assert a.context == PUBLIC
    a.reveal(1)
    assert a.context == restricted("secret.1")
    a.write("board.note", "a text that does not contain the secret")
    assert b.read("board.note") == "a text that does not contain the secret"
    assert b.context == restricted("secret.1")           # paraphrasing does not launder the label
    assert isinstance(b.emit("a different text"), Blocked) and q.emissions == []


def test_labels_accumulate_from_several_sources(store):
    q = new(store=store)
    a = q.session("a", "agent")
    a.reveal(0), a.reveal(2), a.read_external(1)
    assert a.context == restricted("secret.0", "secret.2") | untrusted("external.1")


def test_a_declassifier_does_not_taint_unless_it_fails(store):
    q = new(store=store)
    a = q.session("a", "agent")
    assert a.length(0) == 9 and a.context == PUBLIC
    assert a.emit("the length is 9") == "emitted"
    with pytest.raises(ToolError):
        a.fail(0)                                          # the error message carries the secret
    assert a.context == restricted("secret.0")


def test_direct_messages_carry_the_label_and_the_real_sender(store):
    q = new(store=store)
    a, b = q.session("a", "agent"), q.session("b", "agent")
    a.reveal(0)
    a.send_message("b", "nothing suspicious here")
    assert b.read_messages() == [{"from": "a", "text": "nothing suspicious here"}]
    assert b.context == restricted("secret.0")
    with pytest.raises(ToolError):
        a.send_message("b.other", "x")


def test_a_subagent_inherits_the_label():
    q = new()
    a = q.session("a", "agent")
    a.reveal(1)
    child = a.spawn("child", "agent")
    assert child.context == restricted("secret.1") and isinstance(child.emit("x"), Blocked)


def test_what_is_stored_under_a_restricted_prefix_is_born_restricted():
    @tool(description="Stores a new secret.", params={"value": "Value."})
    def store_secret(call, value: str) -> str:
        call.write("secret.new", value)
        return "ok"

    @tool(description="Reads the new secret.")
    def read_secret(call) -> str:
        return call.read("secret.new")

    policy = Policy.from_dict({"restricted": ["secret."], "sinks": {"emit": []},
                               "roles": {"r": {"tools": ["store_secret", "read_secret", "emit"]}}})
    q = Quorum(policy, (store_secret, read_secret, emit))
    a, b = q.session("a", "r"), q.session("b", "r")
    a.store_secret("xyz")
    assert a.context == PUBLIC and b.read_secret() == "xyz" and b.context == restricted("secret.new")


def test_the_store_does_not_share_objects_with_agents(store):
    q = new(store=store)
    a, b = q.session("a", "agent"), q.session("b", "agent")
    data = {"items": [1, 2]}
    a.write("board.x", data)
    data["items"].append(3)
    seen = b.read("board.x")
    seen["items"].append(4)
    assert b.read("board.x") == {"items": [1, 2]}


# --- gate: enforce and audit -----------------------------------------------------

def test_in_audit_mode_nothing_is_blocked_but_the_decision_is_logged():
    q = new(enforce=False)
    a = q.session("a", "agent")
    a.reveal(0)
    assert a.emit("goes out") == "emitted" and len(q.emissions) == 1
    assert [b["decision"]["policy"] for b in q.blocks()] == ["P1"]
    assert a.trajectory[-1] == {"tool": "emit", "args": {"text": "goes out"}, "result": "emitted"}


def test_when_enforcing_the_agent_sees_the_block_and_nothing_goes_out():
    q = new()
    a = q.session("a", "agent")
    a.reveal(0)
    blocked = a.emit("stays in")
    assert isinstance(blocked, Blocked) and blocked.policy == "P1" and "secret.0" in blocked.reason
    assert q.emissions == [] and a.trajectory[-1]["result"].startswith("BLOCKED by policy P1")


def test_a_user_endorsement_lets_that_source_out():
    q = new(policy=POLICY.evolve(endorsements={"secret.0"}))
    a = q.session("a", "agent")
    a.reveal(0)
    assert a.emit("authorized") == "emitted"
    a.reveal(1)
    assert isinstance(a.emit("not anymore"), Blocked)


def test_the_agent_cannot_grant_human_approval_itself():
    strict_policy = POLICY.evolve(strict_mode=True)
    q = new(policy=strict_policy)
    a = q.session("a", "agent")
    a.read_external(0)
    assert a.emit("x").policy == "P2"
    with pytest.raises(InvalidArguments):                 # there is no such argument
        a.emit("x", human_approval=True)
    seen = []
    q2 = new(policy=strict_policy, approver=lambda s: seen.append(s.principal) or True)
    b = q2.session("b", "agent")
    b.read_external(0)
    assert b.emit("x") == "emitted" and seen == ["b"]
    q3 = new(policy=strict_policy, approver=lambda s: 1 / 0)   # a broken approver denies
    c = q3.session("c", "agent")
    c.read_external(0)
    assert isinstance(c.emit("x"), Blocked)


def test_custom_rules_without_touching_the_core():
    def short_text(s, policy):
        return Decision(False, "X1", "text too long") if len(s.arguments["text"]) > 10 else None
    q = new(rules=(short_text,))
    a = q.session("a", "agent")
    assert a.emit("short") == "emitted" and a.emit("x" * 11).policy == "X1"


# --- access control --------------------------------------------------------------

def test_a_role_can_only_use_its_tools_and_the_attempt_is_logged():
    q = new()
    reader = q.session("reader")
    with pytest.raises(PermissionDenied):
        reader.reveal(0)
    with pytest.raises(PermissionDenied):
        reader.call("emit", text="x")
    assert [e["decision"]["policy"] for e in q.audit_log if e.get("decision")] == ["ROLE", "ROLE"]
    assert q.blocks() == []                                # not a decision of the gate
    assert reader.trajectory[-1]["tool"] == "emit" and "error" in reader.trajectory[-1]
    with pytest.raises(UnknownTool):
        reader.call("does_not_exist")
    with pytest.raises(AttributeError):
        getattr(reader, "does_not_exist")  # noqa: B009


def test_keys_have_permissions_too():
    q = new()
    a, reader = q.session("a", "agent"), q.session("reader")
    with pytest.raises(PermissionDenied):
        a.read("secret.0")                                 # restricted data is not read through the generic door
    with pytest.raises(PermissionDenied):
        a.write("some.thing", 1)
    assert reader.read("board.nothing") is None


def test_quotas_limit_how_many_times_a_tool_is_used():
    q = new(policy=POLICY.evolve(quotas={"length": 2}))
    a, b = q.session("a", "agent"), q.session("b", "agent")
    a.length(0), a.length(1)
    with pytest.raises(QuotaExceeded):
        a.length(2)
    assert b.length(0) == 9                                # the quota is per agent


@pytest.mark.parametrize("args, kwargs", [((), {}), (("0",), {}), ((0, 1), {}), ((), {"j": 0}), ((True,), {})])
def test_arguments_are_validated_against_the_signature(args, kwargs):
    q = new()
    a = q.session("a", "agent")
    with pytest.raises(InvalidArguments):
        a.reveal(*args, **kwargs)
    assert a.context == PUBLIC and "error" in a.trajectory[-1]


# --- configuration: fail at startup, not in production --------------------------

@pytest.mark.parametrize("changes", [
    {"sinks": {}},                                       # there is a sink the policy does not declare
    {"sinks": {"emit": (), "other": ()}},                # the policy declares one that does not exist
    {"declassifiers": {"length"}},                       # an unauthorized declassifier
    {"quotas": {"does_not_exist": 1}},
])
def test_policy_and_tools_must_match(changes):
    with pytest.raises(InvalidConfiguration):
        Quorum(POLICY.evolve(**changes), TOOLS)


def test_other_configuration_errors():
    with pytest.raises(InvalidConfiguration):
        Quorum(POLICY, (*TOOLS, emit))                     # duplicated tool
    with pytest.raises(InvalidConfiguration):
        Quorum(Policy.from_dict({"roles": {"r": {"tools": ["ghost"]}}}), ())
    with pytest.raises(InvalidConfiguration):              # a declassifier must give a rationale
        tool(kind=Kind.DECLASSIFIER, description="x")(lambda call: 1)
    with pytest.raises(InvalidConfiguration):              # every parameter needs a description
        tool(description="x")(lambda call, a: 1)
    q = new()
    q.session("a", "agent")
    for principal, role in [("a", "agent"), ("a.b", "agent"), ("c", "does_not_exist")]:
        with pytest.raises(InvalidConfiguration):
            q.session(principal, role)


# --- audit log -------------------------------------------------------------------

def test_the_audit_log_detects_any_tampering():
    q = new()
    a = q.session("a", "agent")
    a.reveal(0), a.write("board.x", "y"), a.emit("z")
    assert q.audit_log.verify() and len(q.audit_log.to_jsonl().splitlines()) == len(q.audit_log)
    last = q.audit_log[len(q.audit_log) - 1]
    assert last["decision"]["policy"] == "P1" and last["executed"] is False
    assert last["label_before"]["secrets"] == ["secret.0"]
    last["decision"]["allow"] = True
    assert not q.audit_log.verify()


def test_the_audit_log_survives_concurrent_calls():
    q = new()
    sessions = [q.session(f"a{i}", "agent") for i in range(8)]

    def work(s):
        for n in range(40):
            s.write(f"board.{s.principal}", n)
            s.read(f"board.{s.principal}")

    before = len(q.audit_log)
    threads = [threading.Thread(target=work, args=(s,)) for s in sessions]
    [t.start() for t in threads], [t.join() for t in threads]
    assert len(q.audit_log) == before + 8 * 80 and q.audit_log.verify()
