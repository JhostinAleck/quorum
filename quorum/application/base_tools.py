"""Generic tools that are useful in any scenario.

They cover the two channels agents usually communicate through: a shared
key-value space and direct messages. In both, the label travels with the data.
"""
from __future__ import annotations

from typing import Any

from ..domain.errors import require_id
from ..domain.tools import tool
from .monitor import Call


@tool(description="Read a value from the shared space.",
      params={"key": "Key of the value, for example 'notes.summary'."})
def read(call: Call, key: str) -> Any:
    call.require_read(key)
    return call.read(key)


@tool(description="Store a value in the shared space so other agents can read it.",
      params={"key": "Key to store it under.", "data": "Content to store."})
def write(call: Call, key: str, data: Any) -> str:
    call.require_write(key)
    call.write(key, data)
    return "Saved."


@tool(description="Send a direct message to another agent.",
      params={"recipient": "Name of the agent that receives it.", "text": "Content of the message."})
def send_message(call: Call, recipient: str, text: str) -> str:
    require_id(recipient, "recipient")
    number = len(call.keys(f"inbox.{recipient}."))
    call.write(f"inbox.{recipient}.{number:06d}", {"from": call.principal, "text": text})
    return "Sent."


@tool(description="Read the direct messages sent to you.")
def read_messages(call: Call) -> list[dict[str, str]]:
    return [call.read(key) for key in call.keys(f"inbox.{call.principal}.")]


BASE_TOOLS = (read, write, send_message, read_messages)
