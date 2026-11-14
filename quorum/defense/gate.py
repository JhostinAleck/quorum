"""Compuerta de Quórum: función pura que decide si una salida se permite.

No llama a ningún modelo y no lee el texto que se quiere publicar. Decide solo
con la etiqueta del contexto de quien publica.
"""
from __future__ import annotations

from dataclasses import dataclass

from .labels import Etiqueta


@dataclass(frozen=True)
class Decision:
    permitir: bool
    politica: str | None = None
    razon: str = ""


def permitido(
    contexto: Etiqueta,
    endosos: frozenset[str] = frozenset(),
    *,
    modo_estricto: bool = False,
    aprobacion_humana: bool = False,
) -> Decision:
    """Evalúa una llamada a publicar().

    P1: se bloquea si el contexto deriva de fuentes restringidas que el usuario
        no endosó de forma explícita.
    P2 (modo estricto): si el contexto deriva de fuentes no confiables, exige
        aprobación humana.
    """
    sin_endoso = contexto.secretos - endosos
    if sin_endoso:
        return Decision(False, "P1", "fuentes restringidas sin endoso: " + ", ".join(sorted(sin_endoso)))
    if modo_estricto and contexto.no_confiables and not aprobacion_humana:
        return Decision(False, "P2", "contexto no confiable sin aprobación humana: " + ", ".join(sorted(contexto.no_confiables)))
    return Decision(True)
