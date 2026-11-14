"""Generic adapter: works with any framework that supports function calling.

  tool_specs(session)                 the role's tools with their JSON Schema
  execute(session, name, arguments)   runs the tool and always returns text

execute never raises: an error or a block goes back to the model as text,
which is what an agent loop expects.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ..core import Blocked, Session


def tool_specs(session: Session) -> list[dict[str, Any]]:
    return [{"name": tool.name, "description": tool.description, "parameters": tool.schema()}
            for tool in session.tools()]


def to_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, Blocked):
        return str(result)
    return json.dumps(result, ensure_ascii=False, default=str)


def execute(session: Session, name: str, arguments: Mapping[str, Any] | None = None) -> str:
    try:
        return to_text(session.call(name, **dict(arguments or {})))
    except Exception as error:
        return f"ERROR: {error}"
