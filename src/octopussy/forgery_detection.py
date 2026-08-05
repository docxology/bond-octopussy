"""Artifact forgery detection by spectral / UV fingerprinting.

Every painted artifact has a *spectral fingerprint*: its reflectance curve
across the UV-VIS range is a weighted mixture of the pigments that compose
it, and the aged surface emits a characteristic fluorescence under UV light.
A forgery betrays itself in three measurable ways:

1. **Anachronistic pigments** — a modern pigment (e.g. titanium white,
   post-1920) whose introduction post-dates the artifact's claimed era.
   Detection is *residual-based*: fit the measured spectrum to only
   era-consistent pigments and compare with a fit that also allows
   anachronistic ones. When allowing modern pigments dramatically shrinks the
   unexplained residual, the object almost certainly contains them.
2. **UV fluorescence anomaly** — young synthetic varnishes fluoresce brightly
   under UV, whereas aged shellac emits a weak glow.
3. **Unexplained spectral residue** — the era-consistent fit cannot reproduce
   the measurement.

The detector only ever sees *measurements* (a reflectance spectrum plus a UV
reading); it never sees the true pigment mixture. All measurement noise is
drawn from a caller-supplied ``numpy.random.Generator`` so every pipeline is
reproducible under a fixed seed.

This module is pure domain logic (stdlib + numpy), deterministic, and free of
``infrastructure`` and ``bond_api`` imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

__all__ = [
    "ARTIFACT_COUNT",
    "BAND_COUNT",
    "BAND_MAX_NM",
    "BAND_MIN_NM",
    "DEFAULT_EXHIBIT",
    "ForgeryLevel",
    "ForgeryVerdict",
    "PIGMENT_COUNT",
    "PIGMENT_LIBRARY",
    "Pigment",
    "Artifact",
    "SpectrumReading",
    "WAVELENGTH_BANDS",
    "build_uv_response",
    "estimate_mixture",
    "measure_spectrum",
    "mix_spectrum",
    "read_artifact",
    "screen_artifact",
    "screen_collection",
    "screen_reading",
]

#: Spectrophotometer band grid limits (nm) and resolution.
BAND_MIN_NM: float = 320.0
BAND_MAX_NM: float = 760.0
BAND_COUNT: int = 24

#: Wavelength grid (nm) of the UV-VIS spectrophotometer, 320–760 nm.
WAVELENGTH_BANDS: np.ndarray = np.linspace(BAND_MIN_NM, BAND_MAX_NM, BAND_COUNT, dtype=float)
_N_BANDS: int = int(WAVELENGTH_BANDS.size)

#: Weighting of the three evidence channels in the final forgery score.
_ANACH_WEIGHT = 0.5
_UV_WEIGHT = 0.3
_RESIDUAL_WEIGHT = 0.2
#: UV emission above this value flags modern (bright) varnish.
_UV_MID = 0.18
#: Fraction of unexplained residual that maps to a full residual-evidence score.
_RESIDUAL_SATURATION = 0.10

#: Genuine varnish fluorescence (aged shellac), the reference baseline.
_SHELLAC_UV = 0.15


class ForgeryLevel(Enum):
    """Disposition of an artifact after screening."""

    GENUINE = "genuine"
    LIKELY_GENUINE = "likely_genuine"
    LIKELY_FORGED = "likely_forged"
    FORGED = "forged"


@dataclass(frozen=True)
class Pigment:
    """A paint ingredient with a spectral reflectance curve and UV response."""

    name: str
    introduced: int  # year of introduction; 0 = antiquity / unknown-prehistory
    reflectance: np.ndarray  # length N_BANDS, values in [0, 1]
    uv_emission: float  # relative fluorescence under UV, in [0, 1]
    category: str = "pigment"  # "pigment" | "binder" | "varnish"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Pigment.name must be a non-empty string")
        if self.reflectance.shape != (_N_BANDS,):
            raise ValueError(f"Pigment.reflectance must have {_N_BANDS} bands")
        if not (0.0 <= self.uv_emission <= 1.0):
            raise ValueError("Pigment.uv_emission must lie in [0, 1]")


@dataclass(frozen=True)
class Artifact:
    """A painted artifact: identity, claimed era, and true pigment mixture."""

    name: str
    claimed_year: int
    mixture: tuple[tuple[str, float], ...]  # pigment name -> relative weight

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Artifact.name must be a non-empty string")
        if not self.mixture:
            raise ValueError("Artifact.mixture must not be empty")


@dataclass(frozen=True)
class SpectrumReading:
    """What the instrument actually observes: spectrum, UV, and claimed era."""

    spectrum: np.ndarray
    uv: float
    claimed_year: int


@dataclass
class ForgeryVerdict:
    """Result of screening one artifact."""

    artifact: str
    level: ForgeryLevel
    score: float  # 0..1 probability-of-forgery estimate
    anachronistic: tuple[str, ...]
    matched: tuple[tuple[str, float], ...]  # full-fit estimated pigment weights
    reasons: tuple[str, ...]


def _gaussian_peaks(bands: np.ndarray, peaks: list[tuple[float, float, float]]) -> np.ndarray:
    """Sum of Gaussian reflectance peaks over ``bands``, clipped to [0, 1]."""
    spectrum = np.zeros_like(bands, dtype=float)
    for center, width, height in peaks:
        spectrum += height * np.exp(-0.5 * ((bands - center) / width) ** 2)
    return np.asarray(np.clip(spectrum, 0.0, 1.0), dtype=float)


def _tone(constant: float, center: float, width: float, height: float) -> np.ndarray:
    """A mostly-flat tint: a constant baseline plus one Gaussian peak."""
    result: np.ndarray = _gaussian_peaks(WAVELENGTH_BANDS, [(center, width, height)])
    result = result + float(np.clip(constant, 0.0, 1.0))
    return np.asarray(np.clip(result, 0.0, 1.0), dtype=float)


def _build_pigments() -> dict[str, Pigment]:
    """Deterministic built-in pigment library (14 entries)."""
    bands = WAVELENGTH_BANDS
    return {
        "lead_white": Pigment("lead_white", 0, _tone(0.85, 480, 200, 0.06), 0.10),
        "chalk": Pigment("chalk", 0, _tone(0.92, 500, 200, 0.03), 0.08),
        "vermilion": Pigment("vermilion", 0, _gaussian_peaks(bands, [(620, 45, 0.95)]), 0.05),
        "red_ochre": Pigment("red_ochre", 0, _gaussian_peaks(bands, [(650, 80, 0.75)]), 0.06),
        "umber": Pigment("umber", 0, _tone(0.30, 560, 120, 0.15), 0.04),
        "orpiment": Pigment("orpiment", 0, _gaussian_peaks(bands, [(560, 50, 0.90)]), 0.07),
        "cadmium_yellow": Pigment("cadmium_yellow", 1910, _gaussian_peaks(bands, [(580, 45, 0.92)]), 0.06),
        "malachite": Pigment("malachite", 0, _gaussian_peaks(bands, [(520, 55, 0.85)]), 0.05),
        "lapis_lazuli": Pigment("lapis_lazuli", 0, _gaussian_peaks(bands, [(450, 50, 0.88)]), 0.05),
        "phthalocyanine_blue": Pigment("phthalocyanine_blue", 1935, _gaussian_peaks(bands, [(435, 40, 0.96)]), 0.04),
        "titanium_white": Pigment("titanium_white", 1920, _tone(0.98, 480, 200, 0.01), 0.10),
        "egg_tempera": Pigment("egg_tempera", 0, _tone(0.02, 400, 160, 0.10), 0.12, "binder"),
        "shellac_varnish": Pigment("shellac_varnish", 0, _tone(0.25, 620, 120, 0.30), _SHELLAC_UV, "varnish"),
        "acrylic_varnish": Pigment("acrylic_varnish", 1950, _tone(0.20, 560, 140, 0.28), 0.85, "varnish"),
    }


#: Immutable pigment library (deterministic at import time).
PIGMENT_LIBRARY: dict[str, Pigment] = _build_pigments()
PIGMENT_COUNT: int = len(PIGMENT_LIBRARY)


def mix_spectrum(mixture: tuple[tuple[str, float], ...], library: dict[str, Pigment] | None = None) -> np.ndarray:
    """Weighted-sum reflectance spectrum of a pigment mixture (normalized)."""
    lib = PIGMENT_LIBRARY if library is None else library
    weights = np.array([w for _, w in mixture], dtype=float)
    if weights.size == 0 or float(weights.sum()) <= 0.0:
        raise ValueError("artifact mixture must have positive total weight")
    weights = weights / weights.sum()
    spectrum = np.zeros(_N_BANDS, dtype=float)
    for (name, _), w in zip(mixture, weights):
        spectrum += w * np.asarray(lib[name].reflectance, dtype=float)
    return np.clip(spectrum, 0.0, 1.0)


def build_uv_response(mixture: tuple[tuple[str, float], ...], library: dict[str, Pigment] | None = None) -> float:
    """Weighted UV fluorescence response of a pigment mixture."""
    lib = PIGMENT_LIBRARY if library is None else library
    weights = np.array([w for _, w in mixture], dtype=float)
    total = float(weights.sum())
    if total <= 0.0:
        raise ValueError("artifact mixture must have positive total weight")
    response = sum(w * lib[name].uv_emission for (name, _), w in zip(mixture, weights))
    return float(response / total)


def measure_spectrum(
    true_spectrum: np.ndarray,
    *,
    rng: np.random.Generator,
    noise_std: float = 0.02,
) -> np.ndarray:
    """Apply Gaussian measurement noise to a true reflectance spectrum."""
    if true_spectrum.shape != (_N_BANDS,):
        raise ValueError("true_spectrum must be a length-N_BANDS reflectance vector")
    noisy = np.asarray(true_spectrum, dtype=float) + rng.normal(0.0, noise_std, size=_N_BANDS)
    return np.clip(noisy, 0.0, 1.0)


def read_artifact(
    artifact: Artifact,
    *,
    rng: np.random.Generator,
    noise_std: float = 0.02,
    library: dict[str, Pigment] | None = None,
) -> SpectrumReading:
    """Observe an artifact: a noised reflectance spectrum and a noised UV read.

    The detector receives only this reading — never the true mixture.
    """
    truth = mix_spectrum(artifact.mixture, library)
    spectrum = measure_spectrum(truth, rng=rng, noise_std=noise_std)
    uv_true = build_uv_response(artifact.mixture, library)
    uv = float(np.clip(uv_true + rng.normal(0.0, 0.02), 0.0, 1.0))
    return SpectrumReading(spectrum=spectrum, uv=uv, claimed_year=artifact.claimed_year)


def _nnls_fit(
    measured: np.ndarray, columns: np.ndarray, iterations: int, lambd: float = 0.02
) -> tuple[np.ndarray, float, np.ndarray]:
    """Ridge-regularized non-negative least squares via coordinate descent.

    Columns are unit-normalized so fitted weights are on a comparable,
    interpretable scale; the ridge term (``lambd``) suppresses the spurious
    weight-spreading that collinear "white" pigments otherwise produce. Returns
    ``(weights, residual_norm, column_norms)`` where ``weights`` are in the
    normalized basis. Deterministic.
    """
    column_norms = np.sqrt(np.sum(columns * columns, axis=1))
    unit = columns / np.maximum(column_norms, 1e-12)[:, None]
    weights = np.zeros(unit.shape[0], dtype=float)
    target = np.asarray(measured, dtype=float)
    denom = np.sum(unit * unit, axis=1) + lambd
    for _ in range(iterations):
        for j in range(unit.shape[0]):
            residual = target - weights @ unit
            step = float(unit[j] @ residual) * (1.0 / float(denom[j]))
            weights[j] = max(0.0, weights[j] + step)
    residual = target - weights @ unit
    return weights, float(np.linalg.norm(residual)), column_norms


def estimate_mixture(
    measured: np.ndarray,
    library: dict[str, Pigment] | None = None,
    *,
    iterations: int = 400,
) -> dict[str, float]:
    """Estimate pigment abundances for ``measured`` (full library, ridge fit).

    Weights are the unit-basis fitted coefficients renormalized to sum to one,
    giving an interpretable mixture estimate (``name -> fraction``).
    """
    lib = PIGMENT_LIBRARY if library is None else library
    names = sorted(lib)
    matrix = np.stack([np.asarray(lib[n].reflectance, dtype=float) for n in names])
    weights, _, column_norms = _nnls_fit(measured, matrix, iterations)
    abundance = weights / np.maximum(column_norms, 1e-12)
    total = float(abundance.sum())
    if total > 0.0:
        abundance = abundance / total
    return dict(zip(names, [float(w) for w in abundance]))


def _era_consistent_names(library: dict[str, Pigment], claimed_year: int) -> list[str]:
    return sorted(n for n, p in library.items() if p.introduced <= claimed_year)


def screen_reading(
    reading: SpectrumReading,
    library: dict[str, Pigment] | None = None,
    *,
    iterations: int = 400,
) -> ForgeryVerdict:
    """Screen a measured reading and return a forgery disposition + evidence."""
    lib = PIGMENT_LIBRARY if library is None else library
    measured = np.asarray(reading.spectrum, dtype=float)

    full_names = sorted(lib)
    full_matrix = np.stack([np.asarray(lib[n].reflectance, dtype=float) for n in full_names])
    era_names = _era_consistent_names(lib, reading.claimed_year)
    era_matrix = np.stack([np.asarray(lib[n].reflectance, dtype=float) for n in era_names])

    weights_full, residual_full, full_norms = _nnls_fit(measured, full_matrix, iterations)
    weights_era, residual_era, _ = _nnls_fit(measured, era_matrix, iterations)

    # 1) Anachronism evidence. Measure how strongly the era-fit residual (the
    #    part of the spectrum no era-consistent pigment explains) resembles an
    #    anachronistic pigment's distinctive shape (matched filter), and how
    #    much allowing modern pigments shrinks that residual. Both are robust
    #    to the collinearity of flat "white" spectra that corrupts individual
    #    fitted weights.
    era_unit = era_matrix / np.maximum(np.sqrt(np.sum(era_matrix * era_matrix, axis=1)), 1e-12)[:, None]
    era_model = weights_era @ era_unit
    resid_vec = measured - era_model
    resid_norm = float(np.linalg.norm(resid_vec))
    match_score = 0.0
    for name in full_names:
        if lib[name].introduced <= reading.claimed_year:
            continue
        spec = np.asarray(lib[name].reflectance, dtype=float)
        centered = spec - float(spec.mean())
        spec_norm = float(np.linalg.norm(centered)) or 1e-12
        if resid_norm > 1e-12:
            match = abs(float(resid_vec @ centered)) / (resid_norm * spec_norm)
        else:
            match = 0.0
        match_score = max(match_score, match)
    residual_improvement = 0.0
    if residual_era > 1e-12:
        residual_improvement = 1.0 - (residual_full / residual_era) ** 2
    anach_score = float(np.clip(0.7 * match_score + 0.3 * residual_improvement, 0.0, 1.0))

    # 2) UV evidence from the measured fluorescence reading.
    uv_score = float(1.0 / (1.0 + np.exp(-6.0 * (reading.uv - _UV_MID))))

    # 3) Era-consistent residual: unexplained spectrum as a fraction of signal.
    denom = float(np.linalg.norm(measured)) or 1.0
    era_residual_score = min(1.0, residual_era / (_RESIDUAL_SATURATION * denom))

    score = float(
        np.clip(_ANACH_WEIGHT * anach_score + _UV_WEIGHT * uv_score + _RESIDUAL_WEIGHT * era_residual_score, 0.0, 1.0)
    )
    level = _level_for_score(score)

    # Report the fitted composition as renormalized abundance fractions.
    abundance = weights_full / np.maximum(full_norms, 1e-12)
    total = float(abundance.sum())
    if total > 0.0:
        abundance = abundance / total
    matched = tuple((n, float(w)) for n, w in zip(full_names, abundance) if w > 1e-3)
    anachronistic = tuple(
        n for n, w in zip(full_names, abundance) if w > 1e-3 and lib[n].introduced > reading.claimed_year
    )

    reasons = _compose_reasons(anachronistic, anach_score, reading.uv, era_residual_score)
    return ForgeryVerdict(
        artifact="unknown",
        level=level,
        score=score,
        anachronistic=anachronistic,
        matched=matched,
        reasons=tuple(reasons),
    )


def _level_for_score(score: float) -> ForgeryLevel:
    """Map a 0..1 forgery score to a disposition, with calibrated thresholds.

    Thresholds sit inside the measured gaps between the exemplar classes:
    honest objects score < 0.25, a 22-year-anachronism fake scores ~0.35, and
    an all-modern composition scores ~0.45+. These are empirical calibrations
    from the deterministic exemplar exhibit, not free parameters.
    """
    if score < 0.25:
        return ForgeryLevel.GENUINE
    if score < 0.30:
        return ForgeryLevel.LIKELY_GENUINE
    if score < 0.48:
        return ForgeryLevel.LIKELY_FORGED
    return ForgeryLevel.FORGED


def screen_artifact(
    artifact: Artifact,
    library: dict[str, Pigment] | None = None,
    *,
    rng: np.random.Generator,
    noise_std: float = 0.02,
    iterations: int = 400,
) -> ForgeryVerdict:
    """Screen one artifact end-to-end: measure it, then classify the reading."""
    reading = read_artifact(artifact, rng=rng, noise_std=noise_std, library=library)
    verdict = screen_reading(reading, library, iterations=iterations)
    verdict.artifact = artifact.name
    return verdict


def _compose_reasons(
    anachronistic: tuple[str, ...],
    anach_score: float,
    uv_response: float,
    era_residual_score: float,
) -> list[str]:
    """Build human-readable evidence strings for a verdict."""
    reasons: list[str] = []
    if anach_score > 0.05:
        reasons.append(f"anachronistic pigment(s) detected: {', '.join(anachronistic) if anachronistic else 'yes'}")
    if uv_response > _UV_MID:
        reasons.append(f"UV fluorescence anomaly (response {uv_response:.2f})")
    if era_residual_score > 0.4:
        reasons.append("unexplained spectral residue")
    if not reasons:
        reasons.append("spectrum consistent with claimed era")
    return reasons


def screen_collection(
    artifacts: tuple[Artifact, ...],
    library: dict[str, Pigment] | None = None,
    *,
    rng: np.random.Generator,
    noise_std: float = 0.02,
    iterations: int = 400,
) -> tuple[ForgeryVerdict, ...]:
    """Screen a collection of artifacts, returning ordered verdicts."""
    return tuple(screen_artifact(a, library, rng=rng, noise_std=noise_std, iterations=iterations) for a in artifacts)


#: Deterministic exemplar collection used by the mission and offline demos.
DEFAULT_EXHIBIT: tuple[Artifact, ...] = (
    Artifact(
        "tsar_egg", 1910, (("lead_white", 0.35), ("lapis_lazuli", 0.30), ("vermilion", 0.15), ("shellac_varnish", 0.20))
    ),
    Artifact("ballet_case", 1912, (("chalk", 0.4), ("malachite", 0.25), ("umber", 0.15), ("shellac_varnish", 0.20))),
    Artifact("forged_dupe", 1910, (("titanium_white", 0.45), ("phthalocyanine_blue", 0.30), ("acrylic_varnish", 0.25))),
    Artifact("gilt_fake", 1888, (("chalk", 0.5), ("cadmium_yellow", 0.30), ("acrylic_varnish", 0.20))),
)
ARTIFACT_COUNT: int = len(DEFAULT_EXHIBIT)
