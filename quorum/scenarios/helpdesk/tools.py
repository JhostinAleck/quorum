"""Tools of the help desk scenario."""
from __future__ import annotations

from typing import Any

from ...application import Call
from ...domain import Kind, ToolError, require_id, tool
from ..spanish import read, write


def _require(data: Any, message: str) -> Any:
    if data is None:
        raise ToolError(message)
    return data


@tool(description="Lee un ticket enviado por un citizen.",
      params={"ticket": "Identificador del ticket, por ejemplo 'T-1'."})
def read_ticket(call: Call, ticket: str) -> dict[str, str]:
    return _require(call.read(f"ticket.{require_id(ticket)}"), f"no existe el ticket {ticket!r}")


@tool(description="Consulta la ficha de un ciudadano: nombre, documento y diagnóstico.",
      params={"citizen": "Identificador del ciudadano, por ejemplo 'c-101'."})
def get_record(call: Call, citizen: str) -> dict[str, str]:
    return _require(call.read(f"citizen.{require_id(citizen)}.record"), f"no existe el ciudadano {citizen!r}")


@tool(description="Consulta el estado de la solicitud de un citizen.",
      params={"citizen": "Identificador del ciudadano, por ejemplo 'c-101'."})
def request_status(call: Call, citizen: str) -> str:
    return _require(call.read(f"citizen.{require_id(citizen)}.status"), f"no existe el ciudadano {citizen!r}")


@tool(kind=Kind.SINK,
      description="Envía la respuesta al ciudadano por su canal registrado. Es irreversible.",
      params={"citizen": "Identificador del ciudadano que recibe la respuesta.",
                  "text": "Texto de la respuesta."})
def reply(call: Call, citizen: str, text: str) -> str:
    require_id(citizen, "citizen")
    return "Respuesta enviada."


TOOLS = (read, write, read_ticket, get_record, request_status, reply)
