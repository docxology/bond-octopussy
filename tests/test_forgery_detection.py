"""Tests for :mod:`octopussy.forgery_detection` (spectral/UV fingerprinting)."""

from __future__ import annotations

import numpy as np
import pytest

from octopussy import forgery_detection as fg

RNG = np.random.default_rng(7)


def _spectrum() -> np.ndarray:
    return fg.mix_spectrum(fg.DEFAULT_EXHIBIT[0].mixture)


def test_pigment_requires_name():
    with pytest.raises(ValueError):
        fg.Pigment("  ", 0, np.zeros(fg._N_BANDS), 0.1)


def test_pigment_rejects_wrong_shape():
    with pytest.raises(ValueError):
        fg.Pigment("x", 0, np.zeros(3), 0.1)


def test_pigment_rejects_uv_out_of_range():
    with pytest.raises(ValueError):
        fg.Pigment("x", 0, np.zeros(fg._N_BANDS), 1.5)


def test_pigment_library_deterministic():
    assert fg.PIGMENT_COUNT == len(fg.PIGMENT_LIBRARY) == 14
    assert sorted(fg.PIGMENT_LIBRARY) == sorted(fg.PIGMENT_LIBRARY)


def test_artifact_validation():
    with pytest.raises(ValueError):
        fg.Artifact(" ", 1910, (("chalk", 1.0),))
    with pytest.raises(ValueError):
        fg.Artifact("a", 1910, ())


def test_mix_spectrum_shape_and_range():
    spec = _spectrum()
    assert spec.shape == (fg._N_BANDS,)
    assert float(spec.min()) >= 0.0 and float(spec.max()) <= 1.0


def test_mix_spectrum_rejects_empty():
    with pytest.raises(ValueError):
        fg.mix_spectrum(())


def test_mix_spectrum_rejects_zero_weight():
    with pytest.raises(ValueError):
        fg.mix_spectrum((("chalk", 0.0),))


def test_build_uv_response_matches_mixture():
    uv = fg.build_uv_response(fg.DEFAULT_EXHIBIT[2].mixture)
    assert uv > fg.build_uv_response(fg.DEFAULT_EXHIBIT[0].mixture)


def test_build_uv_response_rejects_empty():
    with pytest.raises(ValueError):
        fg.build_uv_response(())


def test_measure_spectrum_rejects_bad_shape():
    with pytest.raises(ValueError):
        fg.measure_spectrum(np.zeros(5), rng=RNG)


def test_measure_spectrum_clips():
    noisy = fg.measure_spectrum(np.zeros(fg._N_BANDS), rng=RNG, noise_std=0.5)
    assert float(noisy.min()) >= 0.0 and float(noisy.max()) <= 1.0


def test_estimate_mixture_recovers_good_fit():
    est = fg.estimate_mixture(fg.mix_spectrum(fg.DEFAULT_EXHIBIT[2].mixture))
    total = sum(est.values())
    assert total > 0.9
    assert set(est) == set(fg.PIGMENT_LIBRARY)


def test_read_artifact_returns_reading():
    reading = fg.read_artifact(fg.DEFAULT_EXHIBIT[0], rng=RNG)
    assert reading.spectrum.shape == (fg._N_BANDS,)
    assert reading.claimed_year == 1910
    assert 0.0 <= reading.uv <= 1.0


def test_genuine_artifacts_not_forged():
    for artifact in fg.DEFAULT_EXHIBIT[:2]:
        verdict = fg.screen_artifact(artifact, rng=np.random.default_rng(3))
        assert verdict.level not in (fg.ForgeryLevel.LIKELY_FORGED, fg.ForgeryLevel.FORGED)
        assert verdict.artifact == artifact.name
        assert verdict.reasons


def test_modern_composition_flagged():
    verdict = fg.screen_artifact(fg.DEFAULT_EXHIBIT[2], rng=np.random.default_rng(3))
    assert verdict.level in (fg.ForgeryLevel.LIKELY_FORGED, fg.ForgeryLevel.FORGED)
    assert verdict.anachronistic


def test_pigments_are_ordered_and_separated():
    genuine = fg.screen_artifact(fg.DEFAULT_EXHIBIT[0], rng=np.random.default_rng(5))
    forged_lite = fg.screen_artifact(fg.DEFAULT_EXHIBIT[3], rng=np.random.default_rng(5))
    forged = fg.screen_artifact(fg.DEFAULT_EXHIBIT[2], rng=np.random.default_rng(5))
    assert genuine.score < forged_lite.score < forged.score


def test_levels_ordered_by_score():
    assert fg._level_for_score(0.10) is fg.ForgeryLevel.GENUINE
    assert fg._level_for_score(0.27) is fg.ForgeryLevel.LIKELY_GENUINE
    assert fg._level_for_score(0.45) is fg.ForgeryLevel.LIKELY_FORGED
    assert fg._level_for_score(0.60) is fg.ForgeryLevel.FORGED


def test_compose_reasons_branches():
    reasons = fg._compose_reasons(("titanium_white",), 0.8, 0.2, 0.1)
    assert any("anachronistic" in r for r in reasons)
    reasons_uv = fg._compose_reasons((), 0.0, 0.6, 0.1)
    assert any("UV" in r for r in reasons_uv)
    reasons_resid = fg._compose_reasons((), 0.0, 0.1, 0.9)
    assert any("residue" in r for r in reasons_resid)
    reasons_ok = fg._compose_reasons((), 0.0, 0.1, 0.1)
    assert any("consistent" in r for r in reasons_ok)


def test_screen_collection_returns_tuple():
    verdicts = fg.screen_collection(fg.DEFAULT_EXHIBIT, rng=RNG)
    assert len(verdicts) == fg.ARTIFACT_COUNT
    empty = fg.screen_collection((), rng=RNG)
    assert empty == ()


def test_screen_reading_round_trip():
    reading = fg.read_artifact(fg.DEFAULT_EXHIBIT[0], rng=RNG)
    verdict = fg.screen_reading(reading)
    assert verdict.level is fg.ForgeryLevel.GENUINE
