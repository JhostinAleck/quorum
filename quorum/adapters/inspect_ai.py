"""Adapter for Inspect AI.

    from quorum.adapters.inspect_ai import inspect_tools
    tools = inspect_tools(session)      # one Inspect Tool per tool of the role

Every call the model makes goes through the Quorum reference monitor, so
labels, permissions and the gate apply exactly as in the scripted episodes.
"""
from __future__ import annotations

from typing import Any

from inspect_ai.tool import Tool as InspectTool
from inspect_ai.tool import ToolDef, ToolParams
from inspect_ai.util import JSONSchema

from ..application import Session
from ..domain import Tool
from .functions import execute


def _wrap(session: Session, tool: Tool) -> InspectTool:
    async def run(**arguments: Any) -> str:
        return execute(session, tool.name, arguments)

    schema = tool.schema()
    params = ToolParams(
        properties={name: JSONSchema.model_validate(prop) for name, prop in schema["properties"].items()},
        required=schema["required"],
    )
    return ToolDef(tool=run, name=tool.name, description=tool.description, parameters=params).as_tool()


def inspect_tools(session: Session) -> list[InspectTool]:
    return [_wrap(session, tool) for tool in session.tools()]
