from hypothesis import given, strategies as st

from quorum.defense.labels import PUBLICA, Conf, Etiqueta, Integ, no_confiable, restringida

ids = st.frozensets(st.sampled_from(["oferta-1", "oferta-2", "anexo-1", "anexo-2"]))
etiquetas = st.builds(Etiqueta, ids, ids)


@given(etiquetas, etiquetas, etiquetas)
def test_unir_es_asociativa(a, b, c):
    assert a.unir(b).unir(c) == a.unir(b.unir(c))


@given(etiquetas, etiquetas)
def test_unir_es_conmutativa(a, b):
    assert a.unir(b) == b.unir(a)


@given(etiquetas)
def test_unir_es_idempotente_y_tiene_neutro(a):
    assert a.unir(a) == a
    assert a.unir(PUBLICA) == a


@given(etiquetas, etiquetas)
def test_unir_nunca_baja_confidencialidad_ni_sube_integridad(a, b):
    u = a.unir(b)
    assert u.conf >= max(a.conf, b.conf)
    assert u.integ <= min(a.integ, b.integ)


def test_niveles():
    assert restringida("oferta-1").conf is Conf.RESTRINGIDO
    assert no_confiable("anexo-1").integ is Integ.NO_CONFIABLE
    assert PUBLICA.conf is Conf.PUBLICO and PUBLICA.integ is Integ.CONFIABLE
