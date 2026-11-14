"""Servicios compartidos del laboratorio, con una etiqueta por valor.

Todo vive en memoria. Los agentes solo pueden tocar los servicios a través de
una Sesion, que es el proxy que propaga etiquetas:
  - leer une la etiqueta del valor al contexto del agente
  - escribir guarda el valor con la etiqueta del contexto
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..defense.gate import Decision, permitido
from ..defense.labels import PUBLICA, Etiqueta, no_confiable, restringida


@dataclass(frozen=True)
class Valor:
    dato: Any
    etiqueta: Etiqueta = PUBLICA


@dataclass
class Laboratorio:
    defensa: bool = True
    modo_estricto: bool = False
    endosos: frozenset[str] = frozenset()
    selladas: dict[str, Valor] = field(default_factory=dict)   # ref -> valor restringido
    anexos: dict[str, Valor] = field(default_factory=dict)     # id -> texto no confiable
    almacen: dict[str, Valor] = field(default_factory=dict)    # registro y evaluación
    portal: list[str] = field(default_factory=list)            # salida al exterior
    bitacora: list[dict] = field(default_factory=list)         # solo anexar

    def sellar(self, ref: str, valor: Any) -> str:
        self.selladas[ref] = Valor(valor, restringida(ref))
        return ref

    def agregar_anexo(self, ident: str, texto: str) -> None:
        self.anexos[ident] = Valor(texto, no_confiable(ident))

    def sesion(self, agente: str) -> "Sesion":
        return Sesion(self, agente)

    def _anotar(self, **evento: Any) -> None:
        self.bitacora.append(evento)


@dataclass
class Sesion:
    lab: Laboratorio
    agente: str
    contexto: Etiqueta = PUBLICA
    trayectoria: list[dict] = field(default_factory=list)

    def _ver(self, valor: Valor) -> Any:
        self.contexto = self.contexto.unir(valor.etiqueta)
        return valor.dato

    def _paso(self, herramienta: str, **args: Any) -> None:
        self.trayectoria.append({"herramienta": herramienta, **args})
        self.lab._anotar(agente=self.agente, herramienta=herramienta, **args)

    # --- lecturas -----------------------------------------------------------
    def leer(self, clave: str) -> Any:
        self._paso("leer", clave=clave)
        valor = self.lab.almacen.get(clave)
        return None if valor is None else self._ver(valor)

    def leer_anexo(self, ident: str) -> str:
        self._paso("leer_anexo", ident=ident)
        return self._ver(self.lab.anexos[ident])

    def abrir(self, ref: str) -> Any:
        """Revela un valor sellado. Contamina el contexto del agente."""
        self._paso("abrir", ref=ref)
        return self._ver(self.lab.selladas[ref])

    # --- desclasificadores declarados ---------------------------------------
    def calcular_puntajes(self, refs: list[str], presupuesto: float) -> dict[str, float]:
        """Puntaje por precio (menor valor, mayor puntaje). Recibe referencias
        opacas y devuelve un resultado público: no contamina el contexto."""
        self._paso("calcular_puntajes", refs=list(refs))
        valores = {r: float(self.lab.selladas[r].dato) for r in refs}
        minimo = min(valores.values())
        return {r: round(100 * minimo / v, 1) if v <= presupuesto else 0.0 for r, v in valores.items()}

    def validar_tope(self, ref: str, presupuesto: float) -> bool:
        self._paso("validar_tope", ref=ref)
        return float(self.lab.selladas[ref].dato) <= presupuesto

    # --- escrituras ---------------------------------------------------------
    def escribir(self, clave: str, dato: Any) -> None:
        self._paso("escribir", clave=clave, dato=dato)
        self.lab.almacen[clave] = Valor(dato, self.contexto)

    def publicar(self, texto: str, *, aprobacion_humana: bool = False) -> Decision:
        decision = permitido(
            self.contexto,
            self.lab.endosos,
            modo_estricto=self.lab.modo_estricto,
            aprobacion_humana=aprobacion_humana,
        )
        salio = decision.permitir or not self.lab.defensa
        self._paso("publicar", texto=texto, permitido=decision.permitir, politica=decision.politica,
                   razon=decision.razon, salio=salio)
        if salio:
            self.lab.portal.append(texto)
        return decision
