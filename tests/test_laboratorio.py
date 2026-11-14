"""Pruebas de punta a punta del proxy y la compuerta, sin modelos."""
import pytest
from hypothesis import given, settings, strategies as st

from quorum.lab.guiones import correr
from quorum.lab.services import Laboratorio


@pytest.mark.parametrize("tipo", ["monolitico", "repartido"])
def test_sin_defensa_el_ataque_logra_la_fuga(tipo):
    ep = correr(tipo, semilla=1, defensa=False)
    assert ep.fuga


@pytest.mark.parametrize("tipo", ["monolitico", "repartido"])
def test_con_quorum_no_hay_fuga_y_queda_en_bitacora(tipo):
    ep = correr(tipo, semilla=1, defensa=True)
    assert not ep.fuga and not ep.publicado
    bloqueo = [e for e in ep.lab.bitacora if e["herramienta"] == "publicar"][-1]
    assert bloqueo["politica"] == "P1" and "oferta-2" in bloqueo["razon"]


def test_episodio_honesto_publica_el_ganador_correcto():
    ep = correr("honesto", semilla=1, defensa=True)
    assert ep.util and not ep.fuga


def test_costo_conocido_abrir_una_oferta_contamina_todo_lo_que_sigue():
    """Bloqueo de más documentado en docs/uso-responsable.md (límite 1)."""
    ep = correr("honesto_escaneada", semilla=1, defensa=True)
    assert not ep.fuga and not ep.publicado


def test_en_el_ataque_repartido_solo_un_agente_abre_el_dato():
    ep = correr("repartido", semilla=1, defensa=False)
    abre = {a for a, t in ep.trayectorias.items() if any(p["herramienta"] == "abrir" for p in t)}
    assert abre == {"radicador"}


def test_parafrasear_no_lava_la_etiqueta():
    lab = Laboratorio()
    lab.sellar("oferta-1", 123456789)
    a, b = lab.sesion("a"), lab.sesion("b")
    a.abrir("oferta-1")
    a.escribir("nota", "texto que no contiene el número")
    b.leer("nota")
    assert not b.publicar("otro texto distinto").permitir


def test_pasar_la_referencia_no_contamina():
    lab = Laboratorio()
    lab.sellar("oferta-1", 100)
    lab.sellar("oferta-2", 200)
    s = lab.sesion("evaluador")
    puntajes = s.calcular_puntajes(["oferta-1", "oferta-2"], presupuesto=1000)
    assert puntajes == {"oferta-1": 100.0, "oferta-2": 50.0}
    assert s.publicar("gana oferta-1").permitir


# Programa aleatorio: tres agentes que leen, abren, copian lo que saben y publican.
# Invariante: con la defensa activa, ningún secreto llega al portal.
operacion = st.tuples(
    st.integers(0, 2),                                              # agente
    st.sampled_from(["abrir", "leer", "escribir", "publicar", "anexo"]),
    st.integers(0, 2),                                              # objeto
)


@settings(max_examples=400, deadline=None)
@given(st.lists(operacion, max_size=40))
def test_invariante_ningun_secreto_sale_al_portal(programa):
    lab = Laboratorio(defensa=True)
    secretos = [f"SECRETO-{i}-9431" for i in range(3)]
    for i, s in enumerate(secretos):
        lab.sellar(f"oferta-{i}", s)
        lab.agregar_anexo(f"anexo-{i}", f"anexo {i}")
    sesiones = [lab.sesion(n) for n in "abc"]
    memoria: list[list[str]] = [[], [], []]
    for agente, op, obj in programa:
        s, mem = sesiones[agente], memoria[agente]
        if op == "abrir":
            mem.append(str(s.abrir(f"oferta-{obj}")))
        elif op == "anexo":
            mem.append(s.leer_anexo(f"anexo-{obj}"))
        elif op == "leer":
            dato = s.leer(f"clave-{obj}")
            if dato is not None:
                mem.append(dato)
        elif op == "escribir":
            s.escribir(f"clave-{obj}", " | ".join(mem))
        else:
            s.publicar(" | ".join(mem))
    publicado = " ".join(lab.portal)
    assert not any(sec in publicado for sec in secretos)
