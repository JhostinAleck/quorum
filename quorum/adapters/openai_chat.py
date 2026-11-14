"""A Chat for the agent loop backed by any OpenAI-compatible endpoint (OpenRouter by default).

The agent loop only wants a function chat(messages, tools) -> assistant
message. This module builds one from the openai client, which is an optional
dependency (the `eval` extra): it is imported when the chat is built, so the
rest of the package works without it and the layer stays provider-free.
"""
from __future__ import annotations

from typing import Any

from .agent_loop import Chat


def _message(response: Any) -> dict[str, Any]:
    """The first choice of a chat completion as a plain dict in the OpenAI format."""
    choices = getattr(response, "choices", None) or []
    reply = getattr(choices[0], "message", None) if choices else None
    message: dict[str, Any] = {"role": "assistant", "content": getattr(reply, "content", None)}
    calls = [{"id": call.id, "type": "function",
              "function": {"name": call.function.name, "arguments": call.function.arguments}}
             for call in getattr(reply, "tool_calls", None) or [] if getattr(call, "function", None) is not None]
    if calls:
        message["tool_calls"] = calls
    return message


def openai_chat(model: str, *, api_key: str, base_url: str = "https://openrouter.ai/api/v1",
                temperature: float = 0.0) -> Chat:
    """Build a chat function that asks `model` for the next assistant message."""
    try:
        from openai import OpenAI
    except ImportError as error:
        raise ImportError("openai_chat needs the 'openai' package, which is optional: "
                          "install the 'eval' extra (uv sync --extra eval)") from error
    client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        offered = {"tools": tools} if tools else {}      # the API rejects an empty list of tools
        response = client.chat.completions.create(model=model, messages=messages, temperature=temperature,
                                                  **offered)
        return _message(response)

    return chat
