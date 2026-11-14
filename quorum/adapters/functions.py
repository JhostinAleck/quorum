"""Generic adapter: works with any framework that supports function calling.

  tool_specs(session)                 the role's tools with their JSON Schema
  execute(session, name, arguments)   runs the tool and always returns text

execute never raises: an error or a block goes back to the model as text,
which is what an agent loop expects.

Both are duck typed. A session whose class has its own tool_specs and execute,
such as a RemoteSession that talks to a monitor in another container, is asked
directly, so an agent loop does not need to know where the monitor runs.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from ..application import Session
from ..domain import Blocked


class ToolSession(Protocol):
    """A session that serves its tools itself, such as a RemoteSession."""

    def tool_specs(self) -> list[dict[str, Any]]: ...

    def execute(self, name: str, arguments: Mapping[str, Any] | None = None) -> str: ...


def _own(session: Session | ToolSession, method: str) -> Callable[..., Any] | None:
    # looked up on the class: on the instance, the sugar of a local Session would
    # answer with a tool that happens to be called 'execute' or 'tool_specs'
    return getattr(type(session), method, None)


def tool_specs(session: Session | ToolSession) -> list[dict[str, Any]]:
    own = _own(session, "tool_specs")
    if own is not None:
        return own(session)
    return [{"name": tool.name, "description": tool.description, "parameters": tool.schema()}
            for tool in session.tools()]


def to_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, Blocked):
        return str(result)
    return json.dumps(result, ensure_ascii=False, default=str)


def execute(session: Session | ToolSession, name: str, arguments: Mapping[str, Any] | None = None) -> str:
    own = _own(session, "execute")
    try:
        if own is not None:
            return own(session, name, arguments)
        return to_text(session.call(name, **dict(arguments or {})))
    except Exception as error:
        return f"ERROR: {error}"
