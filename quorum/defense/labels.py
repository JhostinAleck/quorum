"""Etiquetas de procedencia.

Una etiqueta guarda de qué fuentes restringidas y de qué fuentes no confiables
se derivó un valor. La unión (join) es la unión de conjuntos, así que es
asociativa, conmutativa e idempotente por construcción.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Conf(IntEnum):
    PUBLICO = 0
    RESTRINGIDO = 1


class Integ(IntEnum):
    NO_CONFIABLE = 0
    CONFIABLE = 1


@dataclass(frozen=True)
class Etiqueta:
    secretos: frozenset[str] = frozenset()        # fuentes restringidas
    no_confiables: frozenset[str] = frozenset()   # fuentes escritas por terceros

    @property
    def conf(self) -> Conf:
        return Conf.RESTRINGIDO if self.secretos else Conf.PUBLICO

    @property
    def integ(self) -> Integ:
        return Integ.NO_CONFIABLE if self.no_confiables else Integ.CONFIABLE

    @property
    def fuentes(self) -> frozenset[str]:
        return self.secretos | self.no_confiables

    def unir(self, otra: "Etiqueta") -> "Etiqueta":
        return Etiqueta(self.secretos | otra.secretos, self.no_confiables | otra.no_confiables)


PUBLICA = Etiqueta()


def restringida(fuente: str) -> Etiqueta:
    return Etiqueta(secretos=frozenset({fuente}))


def no_confiable(fuente: str) -> Etiqueta:
    return Etiqueta(no_confiables=frozenset({fuente}))
