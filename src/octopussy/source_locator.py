"""Radiation source localization: weighted nonlinear least squares.

Given a detector lattice with measured count rates and an estimated Poisson
background, this module estimates the position ``(x, y)`` and intensity ``I``
of a concealed emitter whose forward model is

.. math::

    \\mu_i = B + \\frac{I}{(x_i - x)^2 + (y_i - y)^2 + h^2}

with :math:`B` the background rate, :math:`h` the detector standoff, and
:math:`\\mu_i` the expected rate at detector :math:`i`. The estimate is the
weighted nonlinear least-squares solution

.. math::

    \\min_{x,y,I} \\sum_i w_i\\, \\left(c_i - \\mu_i\\right)^2,
    \\qquad w_i = 1/\\sqrt{\\max(c_i, 1)},

solved by **Gauss–Newton** iteration: a numerical Jacobian, the normal
equations with a small Levenberg–Marquardt damping term, and a deterministic
line search (step halving). A fixed data-derived starting point (the excess
weighted centroid) makes the whole solver deterministic — no random state.

:func:`localization_uncertainty` returns an approximate covariance
``(Jᵀ W J)⁻¹`` so the sweep can report positional standard deviations.

Pure domain logic (stdlib + numpy), deterministic, no ``infrastructure`` or
``bond_api`` imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

__all__ = [
    "DetectorLattice",
    "SourceEstimate",
    "excess_counts",
    "gauss_newton_source",
    "localization_uncertainty",
    "locate_from_sweep",
    "model_counts",
    "weighted_residual",
]

#: Numerical-Jacobian central-difference step for each parameter.
_JACOBIAN_EPS = 1e-4
#: Levenberg–Marquardt damping added to the normal-equation diagonal.
_DAMPING = 1e-6
#: Line-search halving steps per Gauss–Newton iteration.
_MAX_LINE_SEARCH = 20


@runtime_checkable
class DetectorLattice(Protocol):
    """Structural contract for anything that lays out detectors in a plane.

    :class:`octopussy.concealment_sweep.SweepGrid` satisfies it. Declaring the
    shape structurally keeps :mod:`source_locator` decoupled from the sweep
    module (no import, no cycle) while still being statically checkable — the
    previous ``grid: object`` signature needed ``type: ignore`` on every
    attribute access.

    ``standoff`` is declared read-only (a property, not a bare annotation) so
    that frozen dataclasses such as ``SweepGrid`` satisfy it — a settable
    protocol variable would reject every immutable implementation.
    """

    @property
    def standoff(self) -> float:
        """Detector elevation above the source plane (m)."""
        ...  # pragma: no cover — typing marker, never executed

    def detector_positions(self) -> np.ndarray:
        """Return an ``(n, 2)`` array of detector ``(x, y)`` positions."""
        ...  # pragma: no cover — typing marker, never executed


@dataclass(frozen=True)
class SourceEstimate:
    """The localized source: position, intensity, and solver diagnostics."""

    position: tuple[float, float]
    intensity: float
    residual_norm: float
    converged: bool
    iterations: int


def excess_counts(counts: np.ndarray, background: float | np.ndarray) -> np.ndarray:
    """Background-subtracted count rates, clamped at zero."""
    counts_arr = np.asarray(counts, dtype=float)
    background_arr = np.asarray(background, dtype=float)
    return np.asarray(np.maximum(counts_arr - background_arr, 0.0), dtype=float)


def model_counts(
    positions: np.ndarray,
    source_xy: tuple[float, float],
    intensity: float,
    background: float,
    standoff: float,
) -> np.ndarray:
    """Forward-model expected rates for every detector position."""
    if intensity < 0.0:
        raise ValueError("intensity must be non-negative")
    if background < 0.0:
        raise ValueError("background must be non-negative")
    if standoff <= 0.0:
        raise ValueError("standoff must be positive")
    dx = positions[:, 0] - source_xy[0]
    dy = positions[:, 1] - source_xy[1]
    radius_sq = dx * dx + dy * dy + standoff * standoff
    return np.asarray(background + intensity / np.maximum(radius_sq, 1e-6), dtype=float)


def weighted_residual(
    params: np.ndarray,
    positions: np.ndarray,
    counts: np.ndarray,
    background: float,
    standoff: float,
) -> np.ndarray:
    """Weighted residual vector for a parameter triple ``(x, y, I)``."""
    predicted = model_counts(positions, (float(params[0]), float(params[1])), float(params[2]), background, standoff)
    weights = 1.0 / np.sqrt(np.maximum(np.asarray(counts, dtype=float), 1.0))
    return np.asarray(weights * (np.asarray(counts, dtype=float) - predicted), dtype=float)


def _numerical_jacobian(
    params: np.ndarray,
    positions: np.ndarray,
    counts: np.ndarray,
    background: float,
    standoff: float,
    eps: float = _JACOBIAN_EPS,
) -> np.ndarray:
    """Central-difference Jacobian of the weighted residual (n x 3)."""
    columns: list[np.ndarray] = []
    for index in range(3):
        plus = params.copy()
        minus = params.copy()
        plus[index] += eps
        if index == 2:
            # Intensity is constrained to be non-negative; clamp the lower
            # perturbation so the boundary point stays feasible. At exactly
            # zero the two points coincide -> a one-sided difference.
            minus[index] = max(0.0, float(minus[index] - eps))
        else:
            minus[index] -= eps
        derivative = (
            weighted_residual(plus, positions, counts, background, standoff)
            - weighted_residual(minus, positions, counts, background, standoff)
        ) / (2.0 * eps)
        columns.append(np.asarray(derivative, dtype=float))
    return np.asarray(np.column_stack(columns), dtype=float)


def _initial_guess(
    positions: np.ndarray,
    counts: np.ndarray,
    background: float,
    standoff: float,
) -> np.ndarray:
    """Data-derived start: excess-weighted centroid plus a scale-matched I."""
    excess = excess_counts(counts, background)
    total = float(excess.sum())
    if total > 1e-12:
        center = np.asarray(
            [float(np.sum(excess * positions[:, 0]) / total), float(np.sum(excess * positions[:, 1]) / total)],
            dtype=float,
        )
    else:
        center = np.asarray([float(np.mean(positions[:, 0])), float(np.mean(positions[:, 1]))], dtype=float)
    peak = float(np.max(excess))
    intensity_guess = peak * standoff * standoff if peak > 0.0 else 0.0
    return np.asarray([center[0], center[1], intensity_guess], dtype=float)


def gauss_newton_source(
    positions: np.ndarray,
    counts: np.ndarray,
    background: float,
    standoff: float,
    *,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> SourceEstimate:
    """Estimate ``(x, y, I)`` by damped Gauss–Newton on the weighted residual.

    Deterministic: the start is the excess-weighted centroid, the Jacobian is
    numerical central differences, the step solves the damped normal equations
    ``(JᵀJ + λI)δ = -Jᵀr`` and is halved until the residual norm decreases.
    """
    if positions.ndim != 2 or positions.shape[1] != 2 or positions.shape[0] == 0:
        raise ValueError("positions must be a non-empty (n, 2) array")
    counts_arr = np.asarray(counts, dtype=float)
    if counts_arr.ndim != 1 or counts_arr.shape[0] != positions.shape[0]:
        raise ValueError("counts must be a length-n vector matching positions")
    if float(np.min(counts_arr)) < 0.0:
        raise ValueError("counts must be non-negative")
    if max_iterations <= 0 or tolerance <= 0.0:
        raise ValueError("max_iterations and tolerance must be positive")

    params = _initial_guess(positions, counts_arr, background, standoff)
    current_norm = float(np.linalg.norm(weighted_residual(params, positions, counts_arr, background, standoff)))
    converged = False
    iteration = 0
    for iteration in range(1, max_iterations + 1):
        jacobian = _numerical_jacobian(params, positions, counts_arr, background, standoff)
        residual = weighted_residual(params, positions, counts_arr, background, standoff)
        normal = jacobian.T @ jacobian
        damped = normal + _DAMPING * np.eye(3)
        rhs = -(jacobian.T @ residual)
        step = np.linalg.solve(damped, rhs)
        step_norm = float(np.linalg.norm(step))
        if step_norm < tolerance:
            converged = True
            break
        candidate = params + step
        candidate[2] = max(0.0, float(candidate[2]))
        candidate_norm = float(
            np.linalg.norm(weighted_residual(candidate, positions, counts_arr, background, standoff))
        )
        halvings = 0
        while candidate_norm >= current_norm and halvings < _MAX_LINE_SEARCH:
            step = step * 0.5
            candidate = params + step
            candidate[2] = max(0.0, float(candidate[2]))
            candidate_norm = float(
                np.linalg.norm(weighted_residual(candidate, positions, counts_arr, background, standoff))
            )
            halvings += 1
        if candidate_norm >= current_norm:
            break  # no improvement possible; stop at the current point
        params = candidate
        current_norm = candidate_norm

    final_residual = float(np.linalg.norm(weighted_residual(params, positions, counts_arr, background, standoff)))
    return SourceEstimate(
        position=(float(params[0]), float(params[1])),
        intensity=float(params[2]),
        residual_norm=final_residual,
        converged=converged,
        iterations=iteration,
    )


def localization_uncertainty(
    positions: np.ndarray,
    counts: np.ndarray,
    background: float,
    estimate: SourceEstimate,
    standoff: float,
) -> tuple[float, float, float]:
    """Approximate parameter standard deviations from ``(JᵀWJ)⁻¹``.

    Returns ``(std_x, std_y, std_intensity)``. A near-singular normal matrix
    (degenerate detector geometry) yields large standard deviations rather
    than a crash.
    """
    params = np.asarray([estimate.position[0], estimate.position[1], estimate.intensity], dtype=float)
    jacobian = _numerical_jacobian(params, positions, counts, background, standoff)
    normal = jacobian.T @ jacobian
    covariance = np.linalg.inv(normal + _DAMPING * np.eye(3))
    diag = np.maximum(np.diag(covariance), 0.0)
    std = np.sqrt(diag)
    return float(std[0]), float(std[1]), float(std[2])


def locate_from_sweep(
    grid: DetectorLattice,
    counts: np.ndarray,
    background: np.ndarray,
    *,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> SourceEstimate:
    """Convenience wrapper: localize a source on a detector lattice.

    Accepts any :class:`DetectorLattice` — anything exposing
    ``detector_positions()`` and ``standoff``, e.g.
    :class:`octopussy.concealment_sweep.SweepGrid`. The per-detector
    ``background`` map is reduced to its mean, matching the flat-background
    forward model in :func:`model_counts`.
    """
    positions: np.ndarray = np.asarray(grid.detector_positions()).astype(np.float64)
    standoff = float(grid.standoff)
    return gauss_newton_source(
        positions,
        np.asarray(counts, dtype=float).ravel(),
        float(np.mean(np.asarray(background, dtype=float))),
        standoff,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
