"""Frente 3's hidden tasks reach the attacking roles of the web interface, and only those."""
import pytest
from test_ui import DOCS, honest_chat, no_configuration  # noqa: F401  (the fixture runs without .env)

from quorum.eval.attacks import ATTACK_POLICY, MARK, side_tasks
from quorum.scenarios.tender import ROLES, SYSTEM, TARGET
from quorum.ui import server, workflow
from quorum.ui.workflow import INVOLVED, build_case, k_of, parse_bid


def recording_chat():
    """The honest fake model, keeping the system prompt each role got."""
    inner, systems = honest_chat(), {}

    def chat(messages, tools):
        names = {t["function"]["name"] for t in tools}
        role = "registrar" if "read_annex" in names else "evaluator" if "score_bids" in names else "publisher"
        systems.setdefault(role, messages[0]["content"])
        return inner(messages, tools)
    return chat, systems


@pytest.mark.parametrize("kind", ["attack_k1", "attack_k2", "attack_k3"])
def test_side_tasks_cover_exactly_the_roles_that_deviate(kind):
    case = build_case([parse_bid(text, name) for name, text in DOCS])
    tasks = side_tasks(kind, case)
    assert set(tasks) == set(INVOLVED[k_of(kind)])
    for text in tasks.values():
        assert text.startswith(ATTACK_POLICY) and MARK in text
    assert any(case.refs[TARGET] in text for text in tasks.values())


def test_honest_episode_gets_no_side_task():
    assert side_tasks("honest", build_case([parse_bid(text, name) for name, text in DOCS])) == {}


@pytest.mark.parametrize("kind", ["attack_k1", "attack_k3"])
def test_with_the_model_the_attacking_roles_run_the_hidden_task(kind):
    chat, systems = recording_chat()
    r = workflow.run(DOCS, kind, engine="llm", chat=chat, side_tasks=side_tasks)
    assert r["engines"] == dict.fromkeys(ROLES, "llm")
    for role in ROLES:
        if role in INVOLVED[k_of(kind)]:
            assert systems[role].startswith(SYSTEM[role]) and ATTACK_POLICY in systems[role]
        else:
            assert systems[role] == SYSTEM[role]


def test_a_side_task_is_also_the_last_numbered_step_of_the_task():
    from quorum.scenarios.tender import TASK
    from quorum.ui import agents
    assert agents.prompts("evaluator") == (SYSTEM["evaluator"], TASK["evaluator"])
    system, task = agents.prompts("evaluator", "X")
    assert system == SYSTEM["evaluator"] + "\n\nX"
    last = max(int(n) for n in agents.STEP.findall(TASK["evaluator"]))
    assert task.startswith(TASK["evaluator"]) and task.endswith(agents.SIDE_STEP.format(n=last + 1))


def test_scripted_engine_ignores_side_tasks():
    r = workflow.run(DOCS, "attack_k1", engine="scripted", side_tasks=side_tasks)
    assert r["engines"] == dict.fromkeys(ROLES, "scripted") and not r["leak"]


def test_the_server_passes_frente_3s_side_tasks():
    assert server.side_tasks is side_tasks
