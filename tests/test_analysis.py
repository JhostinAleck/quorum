"""The tables in metrics.yaml and the ficha come out of datos/ with quorum.eval.analysis."""
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
pytest.importorskip("matplotlib")
from quorum.eval import analysis  # noqa: E402

METRICS = yaml.safe_load((analysis.ROOT / "metrics.yaml").read_text(encoding="utf-8"))["calibracion"]
KEYS = {"m1": "umbral_m1", "m2": "umbral_m2", "m2_blind": "umbral_m2_sin_oraculo",
        "soft_gate": "umbral_compuerta_suave"}


@pytest.fixture(scope="module")
def computed():
    return analysis.compute()


def test_thresholds_match_the_frozen_and_amended_metrics(computed):
    _, results, _ = computed
    gemini, haiku = results.values()
    for arm, key in KEYS.items():
        assert gemini[arm].threshold == METRICS[key]
        assert haiku[arm].threshold == METRICS[key + "_haiku"]


def test_the_headline_numbers(computed):
    eps, results, gate = computed
    assert analysis.leak_by_k(eps) == {1: (5, 10), 2: (6, 10), 3: (5, 10)}
    assert gate.leaks == (16, 16) and sum(e["quorum_blocks"] for e in analysis.honest(eps)) == 0
    gemini, haiku = results.values()
    assert gemini["m2_blind"].leaks == (13, 16) and haiku["m2_blind"].fpr == (5, 30)
    assert haiku["m2"].fpr == (2, 30)


def test_figure_is_written(computed, tmp_path: Path):
    assert analysis.figure(*computed, tmp_path / "f.png").stat().st_size > 10_000
