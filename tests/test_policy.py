from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

import quorum.scenarios as scenarios
from quorum.core import (
    PUBLIC,
    Decision,
    InvalidConfiguration,
    Label,
    Policy,
    Request,
    authorized,
    evaluate,
    restricted,
    untrusted,
)

ids = st.frozensets(st.sampled_from(["s.1", "s.2", "s.3"]))
SIMPLE = Policy(sinks={"emit": ()})


def ask(label, tool="emit", **arguments):
    return Request("agent", "role", tool, arguments, label)


def test_public_passes_and_restricted_is_blocked_by_p1():
    assert evaluate(ask(PUBLIC), SIMPLE).allow
    d = evaluate(ask(restricted("s.2")), SIMPLE)
    assert not d.allow and d.policy == "P1" and "s.2" in d.reason


def test_an_endorsement_releases_only_that_source():
    ctx = restricted("s.1", "s.2")
    assert not evaluate(ask(ctx), SIMPLE.evolve(endorsements={"s.1"})).allow
    assert evaluate(ask(ctx), SIMPLE.evolve(endorsements={"s.1", "s.2"})).allow


@given(ids, ids)
def test_p1_allows_if_and_only_if_every_secret_is_endorsed(secrets, endorsements):
    decision = evaluate(ask(Label(secrets)), SIMPLE.evolve(endorsements=endorsements))
    assert decision.allow == (secrets <= endorsements)


def test_p2_applies_only_in_strict_mode_and_requires_approval():
    ctx = untrusted("external.1")
    assert evaluate(ask(ctx), SIMPLE).allow
    strict_policy = SIMPLE.evolve(strict_mode=True)
    d = evaluate(ask(ctx), strict_policy)
    assert not d.allow and d.policy == "P2"
    assert evaluate(Request("a", "r", "emit", {}, ctx, approved=True), strict_policy).allow


# --- sinks with a recipient: authorization depends on the argument -------------

PER_RECIPIENT = Policy(sinks={"reply": ("client.{client}.",)})


def test_a_sink_accepts_the_data_of_its_own_recipient():
    own = restricted("client.c-1.record", "client.c-1.status")
    assert evaluate(ask(own, "reply", client="c-1"), PER_RECIPIENT).allow
    d = evaluate(ask(own, "reply", client="c-2"), PER_RECIPIENT)
    assert not d.allow and "client.c-1.record" in d.reason
    mixed = own | restricted("client.c-2.record")
    assert not evaluate(ask(mixed, "reply", client="c-1"), PER_RECIPIENT).allow


@pytest.mark.parametrize("value", ["", "c-1.record", "c-1.", ".", "c 1", "{client}", None, True, ["c-1"], 1.5])
def test_the_agent_cannot_widen_the_authorization_with_an_odd_argument(value):
    s = ask(restricted("client.c-1.record"), "reply", client=value)
    assert authorized(s, PER_RECIPIENT) == () and not evaluate(s, PER_RECIPIENT).allow


def test_without_the_argument_there_is_no_authorization():
    assert not evaluate(ask(restricted("client.c-1.record"), "reply"), PER_RECIPIENT).allow


# --- robustness -----------------------------------------------------------------

def test_if_a_rule_fails_the_answer_is_deny():
    def broken(request, policy):
        raise RuntimeError("boom")
    d = evaluate(ask(PUBLIC), SIMPLE, (broken,))
    assert not d.allow and d.policy == "ERROR"


def test_rules_can_be_added_without_touching_the_core():
    def without_attachments(s, policy):
        return Decision(False, "X1", "attachments are not allowed") if "attachment" in s.arguments else None
    assert not evaluate(ask(PUBLIC, attachment="a.pdf"), SIMPLE, (without_attachments,)).allow
    assert evaluate(ask(PUBLIC), SIMPLE, (without_attachments,)).allow


def test_a_misspelled_field_does_not_silently_weaken_the_policy():
    with pytest.raises(InvalidConfiguration):
        Policy.from_dict({"restrictd": ["x."]})
    with pytest.raises(InvalidConfiguration):
        Policy.from_dict({"roles": {"a": {"tool": ["read"]}}})
    with pytest.raises(InvalidConfiguration):
        Policy(quotas={"x": -1})


def test_the_label_is_born_from_the_key():
    p = Policy(restricted=("secret.",), untrusted=("external.",))
    assert p.base_label("secret.1") == restricted("secret.1")
    assert p.base_label("external.1") == untrusted("external.1")
    assert p.base_label("board.1") == PUBLIC


def test_scenario_policies_load_from_toml():
    paths = sorted(Path(scenarios.__file__).parent.glob("*/policy.toml"))
    assert len(paths) >= 2
    for path in paths:
        policy = Policy.from_toml(path)
        assert policy.sinks and policy.roles
