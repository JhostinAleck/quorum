"""A minimal agent loop: a chat model that calls the tools of one session until it is done.

Each agent runs as its own process and reaches the monitor only through its
session, local or remote. The loop is all such a process needs: it offers the
role's tools to the model, runs every call through the monitor and hands the
result back as text. An error or a block is just another tool result, so the
model can read it and react; nothing the model sends can crash the loop.

The model is a plain function, chat(messages, tools) -> assistant message, in
the OpenAI chat format. The loop therefore knows no provider and can be tested
with scripted fakes, without a network.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any

from .functions import execute, tool_specs

Chat = Callable[[list[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]]


def openai_tools(session: Any) -> list[dict[str, Any]]:
    """The tools of the session's role in the OpenAI function-calling format."""
    return [{"type": "function", "function": spec} for spec in tool_specs(session)]


def _text(content: Any) -> str:
    if content is None or isinstance(content, str):
        return content or ""
    return json.dumps(content, ensure_ascii=False, default=str)


def _assistant(reply: Any, turn: int) -> dict[str, Any]:
    """The model's reply as a well-formed assistant message, whatever came back."""
    reply = reply if isinstance(reply, Mapping) else {"content": reply}
    message: dict[str, Any] = {"role": "assistant", "content": _text(reply.get("content"))}
    raw = reply.get("tool_calls")
    calls = []
    for i, call in enumerate(raw if isinstance(raw, (list, tuple)) else ()):
        if not isinstance(call, Mapping):
            continue
        function = call.get("function") if isinstance(call.get("function"), Mapping) else {}
        arguments = function.get("arguments")
        calls.append({"id": _text(call.get("id")) or f"call_{turn}_{i}", "type": "function",
                      "function": {"name": _text(function.get("name")),
                                   "arguments": arguments if isinstance(arguments, str) else _text(arguments)}})
    if calls:
        message["tool_calls"] = calls
    return message


def _run(session: Any, name: str, arguments: str) -> str:
    """Run one tool call. The arguments arrive as a JSON string and must decode to an object."""
    try:
        decoded = json.loads(arguments) if arguments.strip() else {}
    except ValueError as error:
        return f"ERROR: the arguments of {name!r} are not valid JSON ({error})"
    if not isinstance(decoded, dict):
        return f"ERROR: the arguments of {name!r} must be a JSON object, not {type(decoded).__name__}"
    return execute(session, name, decoded)


def run_agent(session: Any, chat: Chat, *, system: str, task: str, max_turns: int = 12) -> list[dict[str, Any]]:
    """Let the model work on the task with the session's tools. Returns the whole conversation.

    A turn is one reply of the model plus the tool calls it asked for. The loop
    ends when the model replies without tool calls, or after max_turns.
    """
    tools = openai_tools(session)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    for turn in range(max_turns):
        message = _assistant(chat(list(messages), tools), turn)
        messages.append(message)
        if "tool_calls" not in message:
            break
        for call in message["tool_calls"]:
            result = _run(session, call["function"]["name"], call["function"]["arguments"])
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    return messages
