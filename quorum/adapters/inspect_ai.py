"""Adapter for Inspect AI.

    from quorum.adapters.inspect_ai import inspect_tools
    tools = inspect_tools(session)      # one Inspect Tool per tool of the role

Every call the model makes goes through the Quorum reference monitor, so
labels, permissions and the gate apply exactly as in the scripted episodes.
The tools are built from tool_specs and execute of the generic adapter, so the
session can be a local Session or a RemoteSession on a monitor in another
container.
"""
from __future__ import annotations

from typing import Any

from inspect_ai.tool import Tool as InspectTool
from inspect_ai.tool import ToolDef, ToolParams
from inspect_ai.util import JSONSchema

from ..application import Session
from .functions import ToolSession, execute, tool_specs


def _wrap(session: Session | ToolSession, spec: dict[str, Any]) -> InspectTool:
    name, schema = spec["name"], spec["parameters"]

    async def run(**arguments: Any) -> str:
        return execute(session, name, arguments)

    params = ToolParams(
        properties={key: JSONSchema.model_validate(prop) for key, prop in schema["properties"].items()},
        required=list(schema.get("required", ())),
    )
    return ToolDef(tool=run, name=name, description=spec["description"], parameters=params).as_tool()


def inspect_tools(session: Session | ToolSession) -> list[InspectTool]:
    return [_wrap(session, spec) for spec in tool_specs(session)]
