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


# --- surface-level dating (measurement -> transmittance -> age -> verdict) ---


def _reference() -> np.ndarray:
    """A plausible unvarnished substrate: a mid-bright, gently sloped ground."""
    return np.linspace(0.45, 0.70, BANDS.size)


def test_measure_varnished_surface_attenuates_the_reference():
    rng = np.random.default_rng(3)
    reference = _reference()
    observed = va.measure_varnished_surface(reference, 120.0, rng=rng, noise_std=0.0)
    # A varnish can only remove light, and it removes most of it in the blue.
    assert float(observed.max()) <= float(reference.max())
    assert observed[0] / reference[0] < observed[-1] / reference[-1]


def test_measure_varnished_surface_validation():
    rng = np.random.default_rng(3)
    with pytest.raises(ValueError):
        va.measure_varnished_surface(np.zeros(3), 10.0, rng=rng)
    with pytest.raises(ValueError):
        va.measure_varnished_surface(_reference(), 10.0, rng=rng, noise_std=-0.1)


def test_recover_transmittance_inverts_the_attenuation():
    rng = np.random.default_rng(5)
    reference = _reference()
    observed = va.measure_varnished_surface(reference, 60.0, rng=rng, noise_std=0.0)
    recovered = va.recover_transmittance(observed, reference)
    np.testing.assert_allclose(recovered, va.varnish_transmittance(BANDS, 60.0), atol=1e-9)


def test_recover_transmittance_validation():
    reference = _reference()
    with pytest.raises(ValueError):
        va.recover_transmittance(np.zeros(3), reference)
    with pytest.raises(ValueError):
        va.recover_transmittance(reference, reference, floor=0.0)
    dark = reference.copy()
    dark[4] = 1e-6  # a band with no usable signal must fail loudly, not silently
    with pytest.raises(ValueError, match="usable floor"):
        va.recover_transmittance(reference, dark)


def test_date_varnished_surface_spans_all_three_verdicts():
    """The dating chain must be able to return every verdict, not just two.

    A pipeline whose construction admits only one outcome proves nothing. Sweep
    the true age of the surface across the decision boundaries and require the
    verdict to actually move: a fresh coat is rejected as too young, a surface
    of the claimed age is consistent, and a much older one is rejected as too
    old.
    """
    reference = _reference()
    verdicts = {}
    for true_age in (3.0, 116.0, 260.0):
        rng = np.random.default_rng(11)
        observed = va.measure_varnished_surface(reference, true_age, rng=rng, noise_std=0.0)
        verdicts[true_age] = va.date_varnished_surface(observed, reference, 1910, 2026).verdict
    assert verdicts[3.0] is va.AgeVerdict.TOO_YOUNG
    assert verdicts[116.0] is va.AgeVerdict.CONSISTENT
    assert verdicts[260.0] is va.AgeVerdict.TOO_OLD
    assert len(set(verdicts.values())) == 3


def test_age_recovery_scatter_is_tight_when_young_and_wide_when_saturated():
    """The saturation limitation the results section reports, as an assertion.

    The yellowing kinetics saturate, so age is well determined for a young film
    and poorly determined for an old one. That is what makes the century-old
    verdict a failure-to-reject rather than a confirmation, so it has to be a
    tested property and not a sentence in the manuscript.
    """
    reference = _reference()
    young = va.age_recovery_scatter(reference, 3.0, rng=np.random.default_rng(21), trials=24)
    old = va.age_recovery_scatter(reference, 116.0, rng=np.random.default_rng(21), trials=24)

    assert young.trials == 24 and len(young.ages) == 24
    assert young.min_age <= young.mean_age <= young.max_age
    # The young film is recovered inside the consistency tolerance every time.
    assert young.within_tolerance == young.trials
    assert young.std_age < 2.0
    # The saturated film is not: its spread exceeds the tolerance it is judged by.
    assert old.std_age > old.tolerance_years
    assert old.within_tolerance < old.trials
    assert old.std_age > 10.0 * young.std_age


def test_age_recovery_scatter_requires_a_real_ensemble():
    with pytest.raises(ValueError, match="at least 2"):
        va.age_recovery_scatter(_reference(), 10.0, rng=np.random.default_rng(1), trials=1)
