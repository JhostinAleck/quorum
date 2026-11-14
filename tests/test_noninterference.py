"""Properties of the monitor over randomly generated programs.

Three agents read secrets and external texts, pass data to each other through
the board and through messages, transform it and try to get it out. The
generator does not know what is dangerous: it tries everything.
"""
from hypothesis import given, settings
from hypothesis import strategies as st
from mini import SECRETS, new

OPERATIONS = ["reveal", "external", "read", "write", "message", "inbox", "emit"]
TRANSFORMS = [
    lambda m: " | ".join(m),
    lambda m: m[-1] if m else "",
    lambda m: m[-1][::-1] if m else "",          # reversed
    lambda m: str(len("".join(m))),              # only the length
    lambda m: "".join(m).upper()[:12],           # a slice
]
programs = st.lists(st.tuples(st.integers(0, 2), st.sampled_from(OPERATIONS), st.integers(0, 2),
                              st.integers(0, len(TRANSFORMS) - 1)), max_size=45)
OTHER_SECRETS = ("one", "two-two", "three-three-three")


def execute(program, *, enforce, secrets=SECRETS):
    q = new(enforce=enforce, secrets=secrets)
    sessions = [q.session(f"a{i}", "agent") for i in range(3)]
    memory = [[], [], []]
    for agent, operation, target, t in program:
        s, m, f = sessions[agent], memory[agent], TRANSFORMS[t]
        if operation == "reveal":
            m.append(s.reveal(target))
        elif operation == "external":
            m.append(s.read_external(target))
        elif operation == "read":
            data = s.read(f"board.{target}")
            if data is not None:
                m.append(data)
        elif operation == "write":
            s.write(f"board.{target}", f(m))
        elif operation == "message":
            s.send_message(f"a{target}", f(m))
        elif operation == "inbox":
            m.extend(x["text"] for x in s.read_messages())
        else:
            s.emit(f(m))
    return q


def emissions(q):
    return [(s.principal, s.arguments["text"]) for s in q.emissions]


def decisions(q):
    return [e["decision"]["allow"] for e in q.audit_log if e.get("tool_kind") == "sink"]


@settings(max_examples=300, deadline=None)
@given(programs)
def test_no_secret_reaches_the_outside(program):
    q = execute(program, enforce=True)
    published = " ".join(text for _, text in emissions(q))
    assert not any(secret in published for secret in SECRETS)
    assert q.audit_log.verify()


@settings(max_examples=300, deadline=None)
@given(programs)
def test_noninterference(program):
    """What leaves the system does not depend on the secrets, not even transformed.

    If changing the secrets changed a single output there would be a leak, even
    if the text of the secret never shows up verbatim.
    """
    assert emissions(execute(program, enforce=True)) == \
        emissions(execute(program, enforce=True, secrets=OTHER_SECRETS))


@settings(max_examples=300, deadline=None)
@given(programs)
def test_auditing_decides_the_same_as_enforcing(program):
    """Justifies measuring with a single run in audit mode: the gate decides the
    same, and what would have gone out is what was audited minus what was blocked."""
    enforced, audited = execute(program, enforce=True), execute(program, enforce=False)
    assert decisions(enforced) == decisions(audited)
    allowed_out = [s for s, allow in zip(emissions(audited), decisions(audited), strict=True) if allow]
    assert emissions(enforced) == allowed_out


@settings(max_examples=150, deadline=None)
@given(programs)
def test_without_defense_the_same_programs_do_leak_sometimes(program):
    """Control: the generator is able to produce leaks. Otherwise the tests
    above would pass vacuously."""
    q = execute(program, enforce=False)
    leak = any(secret in text for _, text in emissions(q) for secret in SECRETS)
    blocked_texts = [text for (_, text), allow in zip(emissions(q), decisions(q), strict=True) if not allow]
    assert leak == any(secret in text for text in blocked_texts for secret in SECRETS)


def test_the_generator_can_produce_leaks():
    """Fixed control: this program leaks a secret if the gate only audits."""
    program = [(0, "reveal", 0, 0), (0, "write", 0, 0), (1, "read", 0, 0), (1, "emit", 0, 0)]
    assert SECRETS[0] in emissions(execute(program, enforce=False))[0][1]
    assert emissions(execute(program, enforce=True)) == []
