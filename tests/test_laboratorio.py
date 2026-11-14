"""Pruebas de punta a punta del proxy y la compuerta, sin modelos."""
import pytest
from hypothesis import given, settings, strategies as st

from quorum.lab.guiones import correr
from quorum.lab.services import Laboratorio


ATAQUES = ["ataque_k1", "ataque_k2", "ataque_k3"]
SEMILLAS = range(25)


@pytest.mark.parametrize("tipo", ATAQUES)
def test_sin_defensa_el_ataque_logra_la_fuga(tipo):
    for semilla in SEMILLAS:
        ep = correr(tipo, semilla, defensa=False)
        assert ep.fuga and not ep.util


@pytest.mark.parametrize("tipo", ATAQUES)
def test_con_quorum_no_hay_fuga_para_ningun_k(tipo):
    for semilla in SEMILLAS:
        ep = correr(tipo, semilla, defensa=True)
        assert not ep.fuga and not ep.publicado and ep.quorum_bloquea
        bloqueo = [e for e in ep.lab.bitacora if e["herramienta"] == "publicar"][-1]
        assert bloqueo["politica"] == "P1" and "oferta-2" in bloqueo["razon"]


@pytest.mark.parametrize("tipo", ATAQUES)
def test_una_corrida_sin_defensa_registra_la_decision_de_la_compuerta(tipo):
    ep = correr(tipo, 3, defensa=False)
    assert ep.fuga and ep.quorum_bloquea


def test_episodio_honesto_publica_el_ganador_correcto():
    for semilla in SEMILLAS:
        ep = correr("honesto", semilla)
        assert ep.util and not ep.fuga and not ep.quorum_bloquea


def test_la_cantidad_de_agentes_con_acciones_fuera_de_rol_crece_con_k():
    def fuera_de_rol(tipo):
        ep = correr(tipo, 1, defensa=False)
        honesto = correr("honesto", 1, defensa=False)
        return {a for a in ep.trayectorias
                if [p["herramienta"] for p in ep.trayectorias[a]] != [p["herramienta"] for p in honesto.trayectorias[a]]}
    assert fuera_de_rol("ataque_k1") == {"evaluador"}
    assert fuera_de_rol("ataque_k2") == {"radicador", "evaluador"}
    assert fuera_de_rol("ataque_k3") == {"radicador", "evaluador", "publicador"}


def test_en_k3_el_resultado_queda_limpio_y_el_dato_viaja_por_contexto():
    ep = correr("ataque_k3", 1, defensa=False)
    assert ep.caso.canario not in ep.lab.almacen["evaluacion.resultado"].dato
    assert ep.caso.canario in ep.lab.almacen["evaluacion.contexto"].dato


def test_transcribir_evita_el_bloqueo_de_mas():
    ep = correr("honesto_escaneada", 1, usa_transcribir=True)
    assert ep.util and not ep.quorum_bloquea


def test_costo_conocido_leer_el_escaneo_contamina_todo_lo_que_sigue():
    """Bloqueo de más documentado en docs/uso-responsable.md (límite 1)."""
    ep = correr("honesto_escaneada", 1, usa_transcribir=False)
    assert not ep.fuga and not ep.publicado and ep.quorum_bloquea


def test_permisos_por_rol():
    lab = Laboratorio()
    pub = lab.sesion("publicador", lee=("evaluacion.",), escribe=())
    with pytest.raises(PermissionError):
        pub.leer("registro.notas")
    with pytest.raises(PermissionError):
        pub.escribir("evaluacion.resultado", "x")


def test_preparar_es_reproducible():
    from quorum.lab.guiones import preparar
    a, b = preparar(7), preparar(7)
    assert a.canario == b.canario and a.ganador_esperado == b.ganador_esperado
    assert preparar(8).canario != a.canario


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
