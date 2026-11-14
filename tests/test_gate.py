from hypothesis import given, strategies as st

from quorum.defense.gate import permitido
from quorum.defense.labels import PUBLICA, Etiqueta, no_confiable, restringida

ids = st.frozensets(st.sampled_from(["oferta-1", "oferta-2", "oferta-3"]))


def test_publico_pasa():
    assert permitido(PUBLICA).permitir


def test_restringido_se_bloquea_con_p1():
    d = permitido(restringida("oferta-2"))
    assert not d.permitir and d.politica == "P1" and "oferta-2" in d.razon


def test_endoso_explicito_libera_solo_esa_fuente():
    ctx = restringida("oferta-1").unir(restringida("oferta-2"))
    assert not permitido(ctx, frozenset({"oferta-1"})).permitir
    assert permitido(ctx, frozenset({"oferta-1", "oferta-2"})).permitir


def test_no_confiable_pasa_salvo_en_modo_estricto():
    ctx = no_confiable("anexo-1")
    assert permitido(ctx).permitir
    d = permitido(ctx, modo_estricto=True)
    assert not d.permitir and d.politica == "P2"
    assert permitido(ctx, modo_estricto=True, aprobacion_humana=True).permitir


@given(ids, ids)
def test_p1_permite_si_y_solo_si_todo_secreto_esta_endosado(secretos, endosos):
    assert permitido(Etiqueta(secretos=secretos), endosos).permitir == (secretos <= endosos)
