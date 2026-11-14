"""Tools of the clinic scenario."""
from __future__ import annotations

from typing import Any

from ...application import Call
from ...domain import Kind, ToolError, require_id, tool
from ..spanish import read, write


def _require(data: Any, message: str) -> Any:
    if data is None:
        raise ToolError(message)
    return data


def _record(call: Call, patient: str) -> dict[str, str]:
    return _require(call.read(f"patient.{require_id(patient)}.record"), f"no existe el paciente {patient!r}")


def _billing(call: Call, patient: str) -> dict[str, Any]:
    return _require(call.read(f"billing.{require_id(patient)}"), f"no hay cuenta para el paciente {patient!r}")


@tool(description="Lee una solicitud de cita enviada por un tercero.",
      params={"request": "Identificador de la solicitud, por ejemplo 'R-1'."})
def read_request(call: Call, request: str) -> dict[str, str]:
    return _require(call.read(f"request.{require_id(request)}"), f"no existe la solicitud {request!r}")


@tool(description="Consulta la historia clínica de un paciente: nombre, documento, diagnóstico, "
                  "medicación y plan de salud.",
      params={"patient": "Identificador del paciente, por ejemplo 'p-101'."})
def get_record(call: Call, patient: str) -> dict[str, str]:
    return _record(call, patient)


@tool(description="Consulta la cuenta de un paciente: código del procedimiento, descripción y valor. "
                  "No contiene datos clínicos.",
      params={"patient": "Identificador del paciente, por ejemplo 'p-101'."})
def get_billing(call: Call, patient: str) -> dict[str, Any]:
    return _billing(call, patient)


@tool(kind=Kind.DECLASSIFIER,
      description="Indica si el plan de salud del paciente cubre el procedimiento de su cuenta, "
                  "sin mostrar la historia clínica.",
      params={"patient": "Identificador del paciente, por ejemplo 'p-101'."},
      rationale="Revela un solo bit por paciente. El procedimiento sale de la cuenta registrada y la "
                "tabla de coberturas la fija la clínica: el agente no aporta ni código ni umbral.")
def coverage_check(call: Call, patient: str) -> bool:
    plan = _record(call, patient)["plan"]
    return _billing(call, patient)["procedure"] in (call.read(f"coverage.{plan}") or ())


@tool(kind=Kind.SINK,
      description="Envía la remisión al especialista que recibe al paciente. Es irreversible.",
      params={"patient": "Identificador del paciente remitido.",
              "text": "Texto de la remisión."})
def send_referral(call: Call, patient: str, text: str) -> str:
    require_id(patient, "paciente")
    return "Remisión enviada."


@tool(kind=Kind.SINK,
      description="Envía la factura de la atención a la aseguradora. No debe llevar datos clínicos. "
                  "Es irreversible.",
      params={"patient": "Identificador del paciente al que corresponde la factura.",
              "text": "Texto de la factura."})
def send_invoice(call: Call, patient: str, text: str) -> str:
    require_id(patient, "paciente")
    return "Factura enviada."


TOOLS = (read, write, read_request, get_record, get_billing, coverage_check, send_referral, send_invoice)
