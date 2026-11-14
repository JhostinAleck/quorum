"""Métricas del barrido: propiedades de la estadística y forma de la salida (backend heurístico, sin red)."""
import pytest

np = pytest.importorskip("numpy")

from analysis.evaluate import BRAZOS, auroc, ic_recalibrado, metricas, puntuar, tabla, umbral, umbrales_boot  # noqa: E402
from quorum.defense.monitors import PROMPT, PROMPT_SIN_PISTA, Heuristico  # noqa: E402
from quorum.lab.scenarios import generar  # noqa: E402


@pytest.fixture(scope="module")
def m():
    eps = generar(40, 10, n_oraculo=9, gemelos=True)
    return metricas(puntuar(eps, Heuristico(), 1), 0.05, 200, 1)


@pytest.mark.parametrize("fpr", [0.01, 0.05, 0.10, 0.5])
def test_el_umbral_vectorizado_coincide_con_el_de_referencia(fpr):
    rng = np.random.default_rng(0)
    for n in (7, 30, 150):
        calib = rng.integers(0, 11, size=n).astype(float)
        idx = rng.integers(0, n, size=(50, n))
        assert list(umbrales_boot(calib, fpr, idx)) == [umbral(list(calib[i]), fpr) for i in idx]


def test_auroc_en_los_casos_extremos():
    rng = np.random.default_rng(0)
    assert auroc(np.array([9., 8.]), np.array([1., 2., 3.]), 100, rng)["valor"] == 1.0
    assert auroc(np.array([5., 5.]), np.array([5., 5., 5.]), 100, rng)["valor"] == 0.5
    assert auroc(np.array([0.]), np.array([4., 6.]), 100, rng)["valor"] == 0.0


def test_recalibrar_el_umbral_ensancha_el_intervalo():
    rng = np.random.default_rng(0)
    calib = np.array([0.] * 27 + [4., 6., 8.])       # el corte del 5 % depende de qué honestos caen
    x = np.array([5.] * 30 + [9.] * 30)
    lo, hi = ic_recalibrado(calib, x, 0.05, 2000, rng)
    assert hi - lo > 0.4                              # con el umbral fijo en 8 sería ~[0,37–0,63]


def test_la_compuerta_bloquea_lo_etiquetado_y_no_ve_el_oraculo(m):
    q = m["quorum"]
    assert q["deteccion"]["valor"] == 1.0 and q["tasa_de_fuga"]["valor"] == 0.0
    assert q["oraculo"]["deteccion"]["valor"] == 0.0 and q["oraculo"]["tasa_de_fuga"]["valor"] > 0
    assert q["oraculo"]["bits_fugados"]["valor"] > q["bits_fugados"]["ataque"]["valor"] == 0.0
    assert q["gemelos"]["discriminacion_pareada"]["valor"] == 0.5 and q["gemelos"]["marcados"]["valor"] == 1.0


def test_la_mezcla_de_trabajo_fija_los_bloqueos_de_la_compuerta(m):
    mz = m["quorum"]["bloqueos_de_mas_por_mezcla"]
    assert mz[0.0] == 0.0 and mz[1.0] == 1.0 and mz[0.25] == pytest.approx(0.25)


def test_todos_los_brazos_traen_las_metricas_nuevas_y_la_tabla_se_arma(m):
    assert list(m) == BRAZOS
    for b, e in m.items():
        assert {"auroc", "gemelos", "oraculo", "bits_fugados", "bloqueos_de_mas_por_mezcla"} <= set(e)
        assert ("deteccion_a_fpr" in e) == (b in ("m1", "m2"))
    assert "Canal del oráculo" in tabla(m)


def test_el_prompt_sin_pista_solo_quita_la_pista():
    assert "radicados" not in PROMPT_SIN_PISTA and len(PROMPT) - len(PROMPT_SIN_PISTA) < 80
