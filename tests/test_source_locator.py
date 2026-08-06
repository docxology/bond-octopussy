"""Tests for :mod:`octopussy.source_locator` (Gauss–Newton localization)."""

from __future__ import annotations

import numpy as np
import pytest

from octopussy import source_locator as sl
from octopussy.concealment_sweep import RadiationSource, SweepGrid, estimate_background, simulate_sweep

TRUE_POS = (7.0, 7.0)
INTENSITY = 800.0


def _scenario(seed: int = 7, grid_size: int = 10):
    grid = SweepGrid((0.0, 0.0), 2.0, grid_size, grid_size)
    positions, counts = simulate_sweep(grid, 40.0, (RadiationSource(TRUE_POS, INTENSITY),), seed=seed)
    background = estimate_background(counts)
    return grid, positions, counts, background


def test_excess_counts_zero_and_positive():
    excess = sl.excess_counts(np.array([5.0, 2.0]), np.array([3.0, 4.0]))
    assert float(excess[0]) == pytest.approx(2.0)
    assert float(excess[1]) == pytest.approx(0.0)  # clamped


def test_model_counts_validation():
    positions = np.array([[0.0, 0.0], [1.0, 1.0]])
    with pytest.raises(ValueError):
        sl.model_counts(positions, (0.0, 0.0), -1.0, 40.0, 1.0)
    with pytest.raises(ValueError):
        sl.model_counts(positions, (0.0, 0.0), 800.0, -1.0, 1.0)
    with pytest.raises(ValueError):
        sl.model_counts(positions, (0.0, 0.0), 800.0, 40.0, 0.0)


def test_model_counts_decreases_with_distance():
    positions = np.array([[0.0, 0.0], [5.0, 0.0]])
    model = sl.model_counts(positions, (0.0, 0.0), 800.0, 40.0, 1.0)
    assert float(model[0]) > float(model[1])


def test_weighted_residual_shapes():
    _, positions, counts, background = _scenario()
    params = np.array([7.0, 7.0, 500.0])
    residual = sl.weighted_residual(params, positions, counts.ravel(), float(np.mean(background)), 1.0)
    assert residual.shape == (counts.size,)


def test_gauss_newton_recovers_position():
    _, positions, counts, background = _scenario()
    estimate = sl.gauss_newton_source(positions, counts.ravel(), float(np.mean(background)), 1.0)
    error = ((estimate.position[0] - TRUE_POS[0]) ** 2 + (estimate.position[1] - TRUE_POS[1]) ** 2) ** 0.5
    assert error < 2.0
    assert estimate.converged
    assert estimate.iterations > 0
    assert estimate.intensity > 0


def test_gauss_newton_deterministic():
    _, positions, counts, background = _scenario()
    a = sl.gauss_newton_source(
        positions, counts.ravel(), float(np.mean(background)), 1.0, max_iterations=50, tolerance=1e-6
    )
    b = sl.gauss_newton_source(
        positions, counts.ravel(), float(np.mean(background)), 1.0, max_iterations=50, tolerance=1e-6
    )
    assert a == b


def test_gauss_newton_validation():
    positions = np.zeros((0, 2))
    with pytest.raises(ValueError):
        sl.gauss_newton_source(positions, np.zeros(0), 40.0, 1.0)
    with pytest.raises(ValueError):
        sl.gauss_newton_source(np.zeros((3, 3)), np.zeros(3), 40.0, 1.0)  # wrong ndim
    pos = np.zeros((3, 2))
    with pytest.raises(ValueError):
        sl.gauss_newton_source(pos, np.zeros(2), 40.0, 1.0)  # counts length mismatch
    with pytest.raises(ValueError):
        sl.gauss_newton_source(pos, np.array([-1.0, 0.0, 0.0]), 40.0, 1.0)  # negative counts
    with pytest.raises(ValueError):
        sl.gauss_newton_source(pos, np.zeros(3), 40.0, 1.0, max_iterations=0)
    with pytest.raises(ValueError):
        sl.gauss_newton_source(pos, np.zeros(3), 40.0, 1.0, tolerance=0.0)


def test_gauss_newton_flat_background_stable():
    # Uniform counts (no source) -> solver still returns a finite estimate.
    grid = SweepGrid((0.0, 0.0), 2.0, 6, 6)
    positions = grid.detector_positions()
    counts = np.full(positions.shape[0], 40.0)
    estimate = sl.gauss_newton_source(positions, counts, 40.0, 1.0)
    assert np.isfinite(estimate.intensity)


def test_initial_guess_zero_excess_uses_mean():
    positions = np.array([[0.0, 0.0], [4.0, 4.0]])
    guess = sl._initial_guess(positions, np.array([40.0, 40.0]), 40.0, 1.0)
    assert guess[0] == pytest.approx(2.0)
    assert guess[1] == pytest.approx(2.0)
    assert guess[2] == pytest.approx(0.0)


def test_localization_uncertainty_positive():
    _, positions, counts, background = _scenario()
    estimate = sl.gauss_newton_source(positions, counts.ravel(), float(np.mean(background)), 1.0)
    stdx, stdy, stdi = sl.localization_uncertainty(positions, counts.ravel(), float(np.mean(background)), estimate, 1.0)
    assert stdx > 0.0 and stdy > 0.0 and stdi > 0.0


def test_locate_from_sweep_wrapper():
    grid, _, counts, background = _scenario()
    estimate = sl.locate_from_sweep(grid, counts, background)
    error = ((estimate.position[0] - TRUE_POS[0]) ** 2 + (estimate.position[1] - TRUE_POS[1]) ** 2) ** 0.5
    assert error < 2.0


def test_sweep_grid_satisfies_detector_lattice_protocol():
    """locate_from_sweep is typed against a structural contract, not `object`."""
    grid, _, _, _ = _scenario()
    assert isinstance(grid, sl.DetectorLattice)
    assert not isinstance(object(), sl.DetectorLattice)


def test_gauss_newton_terminates_without_convergence_on_degenerate_geometry():
    """A near-singular geometry must terminate, not hang, even when it cannot converge.

    The flag "when something goes wrong" path the solver guards: with a
    dominant spike that the damped iteration cannot fit, it must burn the
    iteration budget rather than loop forever, and return a finite estimate.
    """
    positions = np.array([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0], [-3.0, -3.0], [3.0, 3.0]], dtype=float)
    counts = np.array([5.0, 6.0, 5.0, 5.0, 80.0, 5.0], dtype=float)
    est = sl.gauss_newton_source(positions, counts, 4.0, 1.0, max_iterations=50)
    assert est.iterations == 50  # ran to the budget, did not exit early
    assert est.converged is False
    assert all(np.isfinite(est.position)) and np.isfinite(est.intensity)
    assert np.isfinite(est.residual_norm)


def test_gauss_newton_two_detector_degeneracy_is_finite():
    """Two detectors under-determine the source plane but must still terminate."""
    positions = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=float)
    counts = np.array([5.0, 200.0], dtype=float)
    est = sl.gauss_newton_source(positions, counts, 4.0, 1.0)
    assert est.converged is False
    assert all(np.isfinite(est.position))
    assert np.isfinite(est.residual_norm)


def test_gauss_newton_overshooting_start_forces_line_search_halving():
    """A strong source far off-lattice forces the step to overshoot and halve.

    The line-search halving and the no-improvement-stop paths are exactly the
    defensive branches V4 named: they run only when an iteration cannot improve
    the residual. A source well outside the detector lattice throws the initial
    guess off, so the Gauss-Newton step overshoots and the halving loop (and,
    eventually, the stop-at-non-improvement branch) must trigger rather than an
    infinite loop.
    """
    positions = np.column_stack([np.linspace(0.0, 1.0, 3), np.linspace(0.0, 1.0, 3)])
    counts = (4.0 + 10000.0 / ((positions[:, 0] - 8.0) ** 2 + (positions[:, 1] - 8.0) ** 2 + 1.0)).astype(float)
    est = sl.gauss_newton_source(positions, counts, 4.0, 1.0, max_iterations=200, tolerance=1e-20)
    assert est.converged is False
    assert est.iterations == 200
    assert np.isfinite(est.residual_norm)
