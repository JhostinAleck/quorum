import asyncio
import json

import pytest

from quorum.adapters.functions import execute, tool_specs
from quorum.scenarios import helpdesk, tender

SCENARIOS = [(tender, tender.ROLES), (helpdesk, helpdesk.ROLES)]


@pytest.mark.parametrize("scenario, roles", SCENARIOS, ids=["tender", "helpdesk"])
def test_each_role_gets_its_tools_with_a_json_schema(scenario, roles):
    case = scenario.prepare(0)
    for role in roles:
        session = case.quorum.session(role)
        specs = tool_specs(session)
        assert [s["name"] for s in specs] == list(scenario.POLICY.roles[role].tools)
        for spec in specs:
            schema = spec["parameters"]
            assert spec["description"] and schema["type"] == "object" and schema["additionalProperties"] is False
            assert set(schema["required"]) <= set(schema["properties"])
            assert all(p["description"] for p in schema["properties"].values())
            json.dumps(spec)                                 # serializable as is


def test_the_schema_reflects_the_types_of_the_signature():
    case = tender.prepare(0)
    specs = {s["name"]: s["parameters"] for s in tool_specs(case.session("evaluator"))}
    assert specs["score_bids"]["properties"]["refs"]["type"] == "array"
    assert specs["score_bids"]["properties"]["refs"]["items"] == {"type": "string"}
    assert specs["read"]["required"] == ["key"]


def test_execute_never_raises_and_always_returns_text():
    case = tender.prepare(0)
    registrar, publisher = case.session("registrar"), case.session("publisher")
    assert "Andina" in execute(registrar, "read_annex", {"ident": "annex-1"})
    assert execute(registrar, "within_budget", {"ref": "bid-1"}) == "true"
    for name, arguments in [("does_not_exist", {}), ("publish", {"awardee": "x", "text": "y"}),
                            ("open_bid", {}), ("open_bid", {"ref": 7}), ("open_bid", {"ref": "does-not-exist"}),
                            ("read", {"key": "evaluation.result"})]:
        assert execute(registrar, name, arguments).startswith("ERROR: "), name
    registrar.open_bid("bid-2")
    registrar.write("registry.notes", "x")
    assert execute(publisher, "read", {"key": "evaluation.nothing"}) == "null"


def test_a_block_comes_back_to_the_model_as_text():
    case = helpdesk.prepare(0)
    analyst = case.quorum.session("analyst")
    writer = case.quorum.session("writer")
    analyst.write("analysis.reply", analyst.get_record(helpdesk.VICTIM)["document"])
    execute(writer, "read", {"key": "analysis.reply"})
    output = execute(writer, "reply", {"citizen": helpdesk.REQUESTER, "text": "hola"})
    assert output.startswith("BLOCKED by policy P1")


def test_inspect_adapter():
    pytest.importorskip("inspect_ai")
    from inspect_ai.tool import ToolDef

    from quorum.adapters.inspect_ai import inspect_tools

    case = tender.prepare(0)
    registrar = case.session("registrar")
    tools = inspect_tools(registrar)
    definitions = [ToolDef(t) for t in tools]
    assert [d.name for d in definitions] == list(tender.POLICY.roles["registrar"].tools)
    open_bid = next(d for d in definitions if d.name == "open_bid")
    assert open_bid.parameters.required == ["ref"] and open_bid.parameters.properties["ref"].type == "string"
    assert asyncio.run(open_bid.tool(ref="bid-2")) == case.canary
    assert registrar.context.secrets == {"sealed.bid-2"}       # it went through the monitor
    assert asyncio.run(open_bid.tool(ref="does-not-exist")).startswith("ERROR: ")
