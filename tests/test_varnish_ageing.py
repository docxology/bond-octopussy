"""Tests for :mod:`octopussy.varnish_ageing` (Beer–Lambert yellowing kinetics)."""

from __future__ import annotations

import numpy as np
import pytest

from octopussy import varnish_ageing as va

BANDS = va.DEFAULT_BANDS


def test_yellowing_extent_monotonic():
    assert va.yellowing_extent(0.0) == pytest.approx(0.0)
    assert va.yellowing_extent(10.0) > va.yellowing_extent(0.0)
    assert va.yellowing_extent(300.0) > va.yellowing_extent(10.0)
    assert va.yellowing_extent(0.0, tau=10.0, d_max=2.0) == pytest.approx(0.0)


def test_yellowing_extent_validation():
    with pytest.raises(ValueError):
        va.yellowing_extent(-1.0)
    with pytest.raises(ValueError):
        va.yellowing_extent(1.0, tau=0.0)
    with pytest.raises(ValueError):
        va.yellowing_extent(1.0, d_max=0.0)


def test_transmittance_shape_and_range():
    T = va.varnish_transmittance(BANDS, 50.0)
    assert T.shape == BANDS.shape
    assert float(T.min()) >= 0.0 and float(T.max()) <= 1.0


def test_transmittance_decreases_with_age():
    old = va.varnish_transmittance(BANDS, 200.0)
    young = va.varnish_transmittance(BANDS, 5.0)
    assert float(old.min()) < float(young.min())
    # UV/blue end yellows the most.
    assert float(old[0]) < float(old[-1])


def test_estimate_varnish_age_recovers_age():
    for age in (5.0, 50.0, 116.0):
        T = va.varnish_transmittance(BANDS, age)
        estimate, sse = va.estimate_varnish_age(T)
        assert abs(estimate - age) < 5.0
        assert sse < 1e-3


def test_estimate_varnish_age_deterministic():
    T = va.varnish_transmittance(BANDS, 80.0)
    a1, _ = va.estimate_varnish_age(T)
    a2, _ = va.estimate_varnish_age(T)
    assert a1 == a2


def test_estimate_varnish_age_validation():
    with pytest.raises(ValueError):
        va.estimate_varnish_age(np.zeros(3))  # shape mismatch
    with pytest.raises(ValueError):
        va.estimate_varnish_age(np.full(BANDS.shape, 2.0))  # out of [0,1]
    T = va.varnish_transmittance(BANDS, 50.0)
    with pytest.raises(ValueError):
        va.estimate_varnish_age(T, age_max=0.0)
    with pytest.raises(ValueError):
        va.estimate_varnish_age(T, tolerance=0.0)


def test_age_verdict_consistent():
    verdict, closeness = va.age_verdict(1910, 2026, 116.0)
    assert verdict is va.AgeVerdict.CONSISTENT
    assert closeness == pytest.approx(1.0)
    # A one-year offset stays within tolerance but loses closeness.
    verdict2, closeness2 = va.age_verdict(1910, 2026, 115.0)
    assert verdict2 is va.AgeVerdict.CONSISTENT
    assert closeness2 == pytest.approx(0.9913793103448276)


def test_age_verdict_too_young_and_old():
    v1, _ = va.age_verdict(1910, 2026, 5.0)
    assert v1 is va.AgeVerdict.TOO_YOUNG
    v2, _ = va.age_verdict(1910, 2026, 300.0)
    assert v2 is va.AgeVerdict.TOO_OLD


def test_age_verdict_validation():
    with pytest.raises(ValueError):
        va.age_verdict(2026, 2026, 10.0)  # claimed not before current year
    with pytest.raises(ValueError):
        va.age_verdict(1910, 2026, -1.0)
    with pytest.raises(ValueError):
        va.age_verdict(1910, 2026, 50.0, tolerance_years=-1.0)


def test_apply_varnish_aging():
    spectrum = np.linspace(0.3, 0.9, BANDS.size)
    T = va.varnish_transmittance(BANDS, 100.0)
    aged = va.apply_varnish_aging(spectrum, T)
    assert aged.shape == spectrum.shape
    assert float(aged.max()) <= 1.0
    with pytest.raises(ValueError):
        va.apply_varnish_aging(np.zeros(3), T)


def test_assess_varnish_consistent_and_fake():
    genuine_T = va.varnish_transmittance(BANDS, 116.0)
    genuine = va.assess_varnish(genuine_T, 1910, 2026)
    assert genuine.verdict is va.AgeVerdict.CONSISTENT
    assert genuine.expected_age == pytest.approx(116.0)
    assert genuine.reasons

    fake_T = va.varnish_transmittance(BANDS, 3.0)
    fake = va.assess_varnish(fake_T, 1910, 2026)
    assert fake.verdict is va.AgeVerdict.TOO_YOUNG
    assert "younger" in fake.reasons[0]


def test_compose_age_reasons_all_branches():
    too_young = va._compose_age_reasons(va.AgeVerdict.TOO_YOUNG, 3.0, 116.0)
    assert "younger" in too_young[0]
    too_old = va._compose_age_reasons(va.AgeVerdict.TOO_OLD, 300.0, 116.0)
    assert "older" in too_old[0]
    ok = va._compose_age_reasons(va.AgeVerdict.CONSISTENT, 115.0, 116.0)
    assert "consistent" in ok[0]


def test_golden_section_minimize_convex():
    result = va._golden_section_minimize(lambda x: (x - 4.0) ** 2, 0.0, 10.0, 1e-3)
    assert abs(result - 4.0) < 1e-2
