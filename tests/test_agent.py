"""The Agent entity: its context label only grows and its identity is fixed."""
import pytest
from hypothesis import given
from hypothesis import strategies as st
from mini import new

from quorum import PUBLIC, Agent, Label, Role, restricted, untrusted

sources = st.frozensets(st.sampled_from(["a", "b", "c", "d"]), max_size=4)
labels = st.builds(Label, sources, sources)


@given(labels, st.lists(labels, max_size=6))
def test_the_context_never_loses_a_source(start, absorbed):
    agent = Agent("a", Role("r"), start)
    seen = start
    for label in absorbed:
        agent.absorb(label)
        seen = seen | label
        assert seen.flows_to(agent.context) and agent.context.flows_to(seen)
    agent.absorb(PUBLIC)
    assert agent.context == seen


def test_context_role_and_identity_cannot_be_reassigned():
    agent = Agent("a", Role("r"), restricted("s"))
    for attribute, value in (("context", PUBLIC), ("role", Role("admin")), ("principal", "b")):
        with pytest.raises(AttributeError):
            setattr(agent, attribute, value)
    assert agent.context == restricted("s") and agent.role.name == "r" and agent.principal == "a"


def test_the_trajectory_is_a_copy_and_holds_no_labels():
    agent = Agent("a", Role("r"))
    arguments = {"key": "k", "data": ["x"]}
    agent.record("write", arguments, result="Saved.")
    arguments["data"].append("y")                       # later changes do not rewrite history
    agent.trajectory.clear()                            # nor does tampering with what was handed out
    assert agent.trajectory == [{"tool": "write", "args": {"key": "k", "data": ["x"]}, "result": "Saved."}]


def test_a_session_is_an_agent_and_keeps_the_invariant():
    session = new().session("agent")
    assert isinstance(session, Agent)
    session.reveal(0)
    session.read_external(1)
    assert session.context == restricted("secret.0") | untrusted("external.1")
    with pytest.raises(AttributeError):
        session.context = PUBLIC
