"""Varnish ageing kinetics: dating a painted surface from its yellowing.

Natural resin varnishes (shellac, dammar) *yellow* with age: the film's
short-wavelength transmittance decays as chromophores accumulate. The module
models this with a saturating exponential kinetics law (Beer–Lambert
absorption through a film whose absorbing layer grows over time):

.. math::

    d(t) = d_{\\max}\\left(1 - e^{-t/\\tau}\\right),
    \\qquad
    T(\\lambda, t) = e^{-\\alpha(\\lambda)\\,d(t)}

where :math:`\\tau` is the yellowing time constant, :math:`d_{\\max}` the
maximum yellowing extent, and :math:`\\alpha(\\lambda)` the (blue-peaked)
absorption coefficient spectrum.

A *forgery* betrays itself through its varnish: an object claiming to be a
century old whose surface varnish measures only a few years old was
repainted or re-varnished recently. :func:`estimate_varnish_age` inverts the
forward model with a deterministic golden-section least-squares fit over a
bounded age range, and :func:`age_verdict` compares the estimate with the
age the claimed provenance implies.

The instrument does not see :math:`T(\\lambda, t)` directly. It sees a painted
surface — the substrate reflectance *times* the varnish transmittance. The
transmittance is recovered by dividing the varnished measurement by an
unvarnished reference of the same substrate (a cross-section or an unvarnished
edge); :func:`recover_transmittance` does that division and
:func:`date_varnished_surface` runs the whole chain measurement → transmittance
→ age → verdict.

**Precision is age-dependent, and the dependence is severe.** The kinetics
saturate: at :math:`t = 3\\tau` the film has already reached 95% of
:math:`d_{\\max}`, so a further decade of ageing moves the spectrum by less
than the measurement noise. :func:`age_recovery_scatter` measures that effect
directly — it re-observes one surface of *known* age under repeated noise
draws and reports the spread of recovered ages. Any claim about what this
channel establishes has to be read against that spread, not against a single
draw.

Pure domain logic (stdlib + numpy), deterministic given the caller's
``numpy.random.Generator``, no ``infrastructure`` or ``bond_api`` imports.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np

__all__ = [
    "DEFAULT_ABSORPTION_PEAK",
    "DEFAULT_ABSORPTION_CENTER",
    "DEFAULT_ABSORPTION_WIDTH",
    "DEFAULT_BANDS",
    "DEFAULT_D_MAX",
    "DEFAULT_TAU_YEARS",
    "DEFAULT_TOLERANCE_YEARS",
    "DEFAULT_TRIALS",
    "AgeVerdict",
    "RecoveryScatter",
    "VarnishAssessment",
    "age_recovery_scatter",
    "age_verdict",
    "apply_varnish_aging",
    "assess_varnish",
    "date_varnished_surface",
    "estimate_varnish_age",
    "measure_varnished_surface",
    "recover_transmittance",
    "varnish_transmittance",
    "yellowing_extent",
]

#: Default UV-VIS band grid (nm) — matches the forgery spectrophotometer.
DEFAULT_BANDS: np.ndarray = np.linspace(320.0, 760.0, 24, dtype=float)

#: Default yellowing time constant (years) for aged shellac.
DEFAULT_TAU_YEARS = 40.0
#: Default maximum yellowing extent (optical-depth units).
DEFAULT_D_MAX = 1.0
#: Default absorption profile: Gaussian peak in the blue/UV (nm).
DEFAULT_ABSORPTION_PEAK = 0.9
DEFAULT_ABSORPTION_CENTER = 420.0
DEFAULT_ABSORPTION_WIDTH = 80.0
#: Default tolerance for the claimed-era consistency verdict (years).
DEFAULT_TOLERANCE_YEARS = 15.0
#: Bounded age search range for the inverse fit (years).
_AGE_MAX = 300.0
#: Golden-section convergence tolerance on the age axis (years).
_FIT_TOLERANCE = 0.5
#: Default number of noise realizations in a recovery-scatter measurement.
DEFAULT_TRIALS = 32
#: Reference reflectance below which the transmittance ratio is not usable.
_REFERENCE_FLOOR = 1e-2


class AgeVerdict(Enum):
    """Consistency of the measured varnish age with the claimed provenance."""

    CONSISTENT = "consistent"
    TOO_YOUNG = "too_young"  # varnish younger than claimed era -> forgery signal
    TOO_OLD = "too_old"  # varnish older than any plausible provenance


@dataclass(frozen=True)
class VarnishAssessment:
    """The outcome of dating one varnished surface."""

    estimated_age: float  # years
    expected_age: float  # years implied by claimed provenance
    verdict: AgeVerdict
    closeness: float  # 1.0 = exact match, 0.0 = grossly inconsistent
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryScatter:
    """How precisely a *known* varnish age is recovered from a noisy surface.

    This is the estimator's own error bar, measured rather than asserted: one
    surface of known ``true_age`` is re-observed ``trials`` times under
    independent measurement noise and re-dated each time. ``std_age`` is the
    resulting spread and ``within_tolerance`` counts how many realizations
    landed within ``tolerance_years`` of the truth.
    """

    true_age: float
    trials: int
    mean_age: float
    std_age: float
    min_age: float
    max_age: float
    tolerance_years: float
    within_tolerance: int
    ages: tuple[float, ...]


def yellowing_extent(age_years: float, tau: float = DEFAULT_TAU_YEARS, d_max: float = DEFAULT_D_MAX) -> float:
    """Saturating yellowing extent ``d(t) = d_max * (1 - exp(-t/tau))``."""
    if age_years < 0.0:
        raise ValueError("age_years must be non-negative")
    if tau <= 0.0:
        raise ValueError("tau must be positive")
    if d_max <= 0.0:
        raise ValueError("d_max must be positive")
    return float(d_max * (1.0 - math.exp(-float(age_years) / tau)))


def _absorption_profile(
    bands: np.ndarray,
    peak: float = DEFAULT_ABSORPTION_PEAK,
    center: float = DEFAULT_ABSORPTION_CENTER,
    width: float = DEFAULT_ABSORPTION_WIDTH,
) -> np.ndarray:
    """Blue-peaked absorption coefficient spectrum (arbitrary units)."""
    profile = peak * np.exp(-0.5 * ((bands - center) / width) ** 2)
    return np.asarray(profile, dtype=float)


def varnish_transmittance(
    bands: np.ndarray,
    age_years: float,
    tau: float = DEFAULT_TAU_YEARS,
    d_max: float = DEFAULT_D_MAX,
    peak: float = DEFAULT_ABSORPTION_PEAK,
    center: float = DEFAULT_ABSORPTION_CENTER,
    width: float = DEFAULT_ABSORPTION_WIDTH,
) -> np.ndarray:
    """Beer–Lambert transmittance of a varnish film of age ``age_years``."""
    extent = yellowing_extent(age_years, tau, d_max)
    absorption = _absorption_profile(bands, peak, center, width)
    return np.asarray(np.exp(-absorption * extent), dtype=float)


def _transmittance_sse(
    age_years: float,
    measured: np.ndarray,
    bands: np.ndarray,
    tau: float,
    d_max: float,
    peak: float,
    center: float,
    width: float,
) -> float:
    """Sum of squared residuals between model and measured transmittance."""
    model = varnish_transmittance(bands, age_years, tau, d_max, peak, center, width)
    residual = np.asarray(model, dtype=float) - np.asarray(measured, dtype=float)
    return float(np.sum(residual * residual))


def _golden_section_minimize(
    fn: Callable[[float], float],
    low: float,
    high: float,
    tolerance: float,
) -> float:
    """Deterministic bounded golden-section minimizer for a float->float fn."""
    inv_phi = (math.sqrt(5.0) - 1.0) / 2.0
    left = low
    right = high
    x1 = right - inv_phi * (right - left)
    x2 = left + inv_phi * (right - left)
    f1 = fn(x1)
    f2 = fn(x2)
    while right - left > tolerance:
        if f1 < f2:
            right = x2
            x2 = x1
            f2 = f1
            x1 = right - inv_phi * (right - left)
            f1 = fn(x1)
        else:
            left = x1
            x1 = x2
            f1 = f2
            x2 = left + inv_phi * (right - left)
            f2 = fn(x2)
    return (left + right) / 2.0


def estimate_varnish_age(
    measured_transmittance: np.ndarray,
    bands: np.ndarray = DEFAULT_BANDS,
    *,
    tau: float = DEFAULT_TAU_YEARS,
    d_max: float = DEFAULT_D_MAX,
    peak: float = DEFAULT_ABSORPTION_PEAK,
    center: float = DEFAULT_ABSORPTION_CENTER,
    width: float = DEFAULT_ABSORPTION_WIDTH,
    age_max: float = _AGE_MAX,
    tolerance: float = _FIT_TOLERANCE,
) -> tuple[float, float]:
    """Invert the yellowing model: estimate the varnish age from a measurement.

    Returns ``(estimated_age_years, residual_sse)``. The fit is a bounded
    golden-section search over ``[0, age_max]`` — deterministic, derivative-free,
    and independent of any random state.
    """
    measured = np.asarray(measured_transmittance, dtype=float)
    if measured.shape != bands.shape:
        raise ValueError("measured_transmittance must match the band grid shape")
    if not (0.0 <= float(measured.min()) and float(measured.max()) <= 1.0):
        raise ValueError("transmittance values must lie in [0, 1]")
    if age_max <= 0.0 or tolerance <= 0.0:
        raise ValueError("age_max and tolerance must be positive")

    def objective(age: float) -> float:
        return _transmittance_sse(age, measured, bands, tau, d_max, peak, center, width)

    age_hat = _golden_section_minimize(objective, 0.0, age_max, tolerance)
    sse = objective(age_hat)
    return float(age_hat), float(sse)


def age_verdict(
    claimed_year: int,
    current_year: int,
    estimated_age: float,
    *,
    tolerance_years: float = DEFAULT_TOLERANCE_YEARS,
) -> tuple[AgeVerdict, float]:
    """Judge whether an estimated varnish age matches the claimed provenance.

    Returns ``(verdict, closeness)`` where ``closeness`` is 1.0 for an exact
    match and decays to 0.0 as the mismatch grows past the tolerance.
    """
    expected_age = float(current_year - claimed_year)
    if expected_age <= 0.0:
        raise ValueError("claimed provenance must predate the current year")
    if estimated_age < 0.0:
        raise ValueError("estimated_age must be non-negative")
    if tolerance_years < 0.0:
        raise ValueError("tolerance_years must be non-negative")
    difference = estimated_age - expected_age
    if difference < -tolerance_years:
        verdict = AgeVerdict.TOO_YOUNG
    elif difference > tolerance_years:
        verdict = AgeVerdict.TOO_OLD
    else:
        verdict = AgeVerdict.CONSISTENT
    closeness = max(0.0, 1.0 - abs(difference) / max(expected_age, 1.0))
    return verdict, float(closeness)


def apply_varnish_aging(spectrum: np.ndarray, transmittance: np.ndarray) -> np.ndarray:
    """Multiply a reflectance spectrum by a varnish transmittance (aged surface)."""
    if spectrum.shape != transmittance.shape:
        raise ValueError("spectrum and transmittance must share the band grid shape")
    return np.asarray(
        np.clip(np.asarray(spectrum, dtype=float) * np.asarray(transmittance, dtype=float), 0.0, 1.0), dtype=float
    )


def assess_varnish(
    measured_transmittance: np.ndarray,
    claimed_year: int,
    current_year: int,
    bands: np.ndarray = DEFAULT_BANDS,
    *,
    tau: float = DEFAULT_TAU_YEARS,
    d_max: float = DEFAULT_D_MAX,
    peak: float = DEFAULT_ABSORPTION_PEAK,
    center: float = DEFAULT_ABSORPTION_CENTER,
    width: float = DEFAULT_ABSORPTION_WIDTH,
    tolerance_years: float = DEFAULT_TOLERANCE_YEARS,
    age_max: float = _AGE_MAX,
    fit_tolerance: float = _FIT_TOLERANCE,
) -> VarnishAssessment:
    """Full varnish dating: estimate the age, then judge the claimed era."""
    estimated_age, _ = estimate_varnish_age(
        measured_transmittance,
        bands,
        tau=tau,
        d_max=d_max,
        peak=peak,
        center=center,
        width=width,
        age_max=age_max,
        tolerance=fit_tolerance,
    )
    verdict, closeness = age_verdict(claimed_year, current_year, estimated_age, tolerance_years=tolerance_years)
    expected = float(current_year - claimed_year)
    reasons = _compose_age_reasons(verdict, estimated_age, expected)
    return VarnishAssessment(
        estimated_age=float(estimated_age),
        expected_age=expected,
        verdict=verdict,
        closeness=float(closeness),
        reasons=tuple(reasons),
    )


def measure_varnished_surface(
    reference_reflectance: np.ndarray,
    age_years: float,
    *,
    rng: np.random.Generator,
    noise_std: float = 0.02,
    bands: np.ndarray = DEFAULT_BANDS,
    tau: float = DEFAULT_TAU_YEARS,
    d_max: float = DEFAULT_D_MAX,
    peak: float = DEFAULT_ABSORPTION_PEAK,
    center: float = DEFAULT_ABSORPTION_CENTER,
    width: float = DEFAULT_ABSORPTION_WIDTH,
) -> np.ndarray:
    """Observe a varnished surface: substrate reflectance attenuated by the film.

    ``reference_reflectance`` is the *unvarnished* substrate — for an exhibit
    artifact, the reflectance its pigment mixture alone would give. The
    instrument sees that curve multiplied by the transmittance of a varnish
    film of ``age_years``, plus Gaussian measurement noise from the caller's
    generator. This is the forward model that
    :func:`date_varnished_surface` inverts.
    """
    reference = np.asarray(reference_reflectance, dtype=float)
    if reference.shape != bands.shape:
        raise ValueError("reference_reflectance must match the band grid shape")
    if noise_std < 0.0:
        raise ValueError("noise_std must be non-negative")
    transmittance = varnish_transmittance(bands, age_years, tau, d_max, peak, center, width)
    observed = reference * transmittance + rng.normal(0.0, noise_std, size=bands.size)
    return np.asarray(np.clip(observed, 0.0, 1.0), dtype=float)


def recover_transmittance(
    measured_reflectance: np.ndarray,
    reference_reflectance: np.ndarray,
    *,
    floor: float = _REFERENCE_FLOOR,
) -> np.ndarray:
    """Divide a varnished measurement by its unvarnished reference.

    Band-wise inverse of :func:`apply_varnish_aging`. A band whose reference
    reflectance falls below ``floor`` carries no usable signal — the ratio
    would amplify noise without bound — so it is rejected loudly rather than
    silently clipped to something that looks like a measurement.
    """
    measured = np.asarray(measured_reflectance, dtype=float)
    reference = np.asarray(reference_reflectance, dtype=float)
    if measured.shape != reference.shape:
        raise ValueError("measured and reference reflectance must share the band grid shape")
    if floor <= 0.0:
        raise ValueError("floor must be positive")
    if float(reference.min()) < floor:
        raise ValueError(f"reference reflectance drops below the usable floor {floor}")
    return np.asarray(np.clip(measured / reference, 0.0, 1.0), dtype=float)


def date_varnished_surface(
    measured_reflectance: np.ndarray,
    reference_reflectance: np.ndarray,
    claimed_year: int,
    current_year: int,
    bands: np.ndarray = DEFAULT_BANDS,
    *,
    tau: float = DEFAULT_TAU_YEARS,
    d_max: float = DEFAULT_D_MAX,
    peak: float = DEFAULT_ABSORPTION_PEAK,
    center: float = DEFAULT_ABSORPTION_CENTER,
    width: float = DEFAULT_ABSORPTION_WIDTH,
    tolerance_years: float = DEFAULT_TOLERANCE_YEARS,
    age_max: float = _AGE_MAX,
    fit_tolerance: float = _FIT_TOLERANCE,
    floor: float = _REFERENCE_FLOOR,
) -> VarnishAssessment:
    """Date a painted surface end-to-end: measurement → transmittance → verdict.

    The full chain an examiner runs: recover the film's transmittance from the
    varnished measurement and its unvarnished reference, invert the yellowing
    kinetics for an age, and judge that age against the claimed provenance.
    """
    transmittance = recover_transmittance(measured_reflectance, reference_reflectance, floor=floor)
    return assess_varnish(
        transmittance,
        claimed_year,
        current_year,
        bands,
        tau=tau,
        d_max=d_max,
        peak=peak,
        center=center,
        width=width,
        tolerance_years=tolerance_years,
        age_max=age_max,
        fit_tolerance=fit_tolerance,
    )


def age_recovery_scatter(
    reference_reflectance: np.ndarray,
    true_age: float,
    *,
    rng: np.random.Generator,
    trials: int = DEFAULT_TRIALS,
    noise_std: float = 0.02,
    bands: np.ndarray = DEFAULT_BANDS,
    tolerance_years: float = DEFAULT_TOLERANCE_YEARS,
    tau: float = DEFAULT_TAU_YEARS,
    d_max: float = DEFAULT_D_MAX,
    peak: float = DEFAULT_ABSORPTION_PEAK,
    center: float = DEFAULT_ABSORPTION_CENTER,
    width: float = DEFAULT_ABSORPTION_WIDTH,
    age_max: float = _AGE_MAX,
    fit_tolerance: float = _FIT_TOLERANCE,
    floor: float = _REFERENCE_FLOOR,
) -> RecoveryScatter:
    """Measure the estimator's error bar at ``true_age`` by repeated observation.

    Re-observes one surface of known age ``trials`` times under independent
    measurement noise and re-dates each observation. The returned spread is the
    honest uncertainty on any single dating of a surface like this one — and
    because the yellowing kinetics saturate, it grows sharply with ``true_age``.
    """
    if trials < 2:
        raise ValueError("trials must be at least 2 for a scatter estimate")
    recovered: list[float] = []
    for _ in range(trials):
        measured = measure_varnished_surface(
            reference_reflectance,
            true_age,
            rng=rng,
            noise_std=noise_std,
            bands=bands,
            tau=tau,
            d_max=d_max,
            peak=peak,
            center=center,
            width=width,
        )
        transmittance = recover_transmittance(measured, reference_reflectance, floor=floor)
        age, _sse = estimate_varnish_age(
            transmittance,
            bands,
            tau=tau,
            d_max=d_max,
            peak=peak,
            center=center,
            width=width,
            age_max=age_max,
            tolerance=fit_tolerance,
        )
        recovered.append(float(age))
    ages = np.asarray(recovered, dtype=float)
    return RecoveryScatter(
        true_age=float(true_age),
        trials=int(trials),
        mean_age=float(ages.mean()),
        std_age=float(ages.std()),
        min_age=float(ages.min()),
        max_age=float(ages.max()),
        tolerance_years=float(tolerance_years),
        within_tolerance=int(np.sum(np.abs(ages - float(true_age)) <= tolerance_years)),
        ages=tuple(float(a) for a in ages),
    )


def _compose_age_reasons(verdict: AgeVerdict, estimated_age: float, expected_age: float) -> list[str]:
    """Human-readable evidence strings for a varnish-age assessment."""
    if verdict is AgeVerdict.TOO_YOUNG:
        return [f"varnish measures ~{estimated_age:.0f} years, far younger than the claimed {expected_age:.0f}"]
    if verdict is AgeVerdict.TOO_OLD:
        return [f"varnish measures ~{estimated_age:.0f} years, older than the claimed {expected_age:.0f}"]
    return [f"varnish age (~{estimated_age:.0f} years) is consistent with the claimed {expected_age:.0f}"]
