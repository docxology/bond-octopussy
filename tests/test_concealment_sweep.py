"""Tests for :mod:`octopussy.concealment_sweep` (radiation + mass anomaly)."""

from __future__ import annotations

import numpy as np
import pytest

from octopussy import concealment_sweep as cs


def _grid() -> cs.SweepGrid:
    return cs.SweepGrid((0.0, 0.0), 2.0, 8, 8)


def test_sweep_grid_validation():
    with pytest.raises(ValueError):
        cs.SweepGrid((0.0, 0.0), 0.0, 8, 8)
    with pytest.raises(ValueError):
        cs.SweepGrid((0.0, 0.0), 2.0, 0, 8)
    with pytest.raises(ValueError):
        cs.SweepGrid((0.0, 0.0), 2.0, 8, -3)
    with pytest.raises(ValueError):
        cs.SweepGrid((0.0, 0.0), 2.0, 8, 8, standoff=0.0)


def test_detector_positions_shape():
    pos = _grid().detector_positions()
    assert pos.shape == (64, 2)


def test_simulate_sweep_rejects_negative_background():
    with pytest.raises(ValueError):
        cs.simulate_sweep(_grid(), -1.0, (), seed=7)


def test_simulate_sweep_deterministic():
    a = cs.simulate_sweep(_grid(), 40.0, (), seed=7)
    b = cs.simulate_sweep(_grid(), 40.0, (), seed=7)
    assert np.array_equal(a[1], b[1])


def test_simulate_sweep_with_source_raises_hotspot():
    grid = _grid()
    source = (cs.RadiationSource((7.0, 7.0), 600.0),)
    _, counts = cs.simulate_sweep(grid, 40.0, source, seed=7)
    background = cs.estimate_background(counts)
    anomaly = cs.anomaly_map(counts, background)
    hits = cs.detect_hotspots(counts, anomaly, 3.0)
    assert hits


def test_estimate_background_rejects_bad_shape():
    with pytest.raises(ValueError):
        cs.estimate_background(np.zeros((1,)))


def test_anomaly_map_shape():
    counts = cs.simulate_sweep(_grid(), 40.0, (), seed=7)[1]
    bg = cs.estimate_background(counts)
    anom = cs.anomaly_map(counts, bg)
    assert anom.shape == counts.shape


def test_detect_hotspots_no_hits_clear_background():
    counts = cs.simulate_sweep(_grid(), 40.0, (), seed=1)[1]
    bg = cs.estimate_background(counts)
    anom = cs.anomaly_map(counts, bg)
    hits = cs.detect_hotspots(counts, anom, 6.0)
    assert hits == ()


def test_detect_hotspots_min_score_filter():
    counts = cs.simulate_sweep(_grid(), 40.0, (cs.RadiationSource((7.0, 7.0), 600.0),), seed=7)[1]
    bg = cs.estimate_background(counts)
    anom = cs.anomaly_map(counts, bg)
    all_hits = cs.detect_hotspots(counts, anom, 0.5)
    filtered = cs.detect_hotspots(counts, anom, 0.5, min_score=10.0)
    assert len(filtered) <= len(all_hits)


def test_container_validation():
    with pytest.raises(ValueError):
        cs.Container("  ", 0.1, 1.0, "crate")
    with pytest.raises(ValueError):
        cs.Container("x", 0.0, 1.0, "crate")
    with pytest.raises(ValueError):
        cs.Container("x", 0.1, -1.0, "crate")


def test_mass_anomaly_known_category():
    result = cs.mass_anomaly(cs.Container("royal_egg", 0.002, 7.5, "egg"))
    assert result.name == "royal_egg"
    assert result.expected_mass_kg > 0
    assert result.mass_z > 0
    assert result.density_ratio > 1.0


def test_mass_anomaly_unknown_category():
    with pytest.raises(KeyError):
        cs.mass_anomaly(cs.Container("x", 0.1, 1.0, "hovercraft"))


def test_fuse_report_mass_flagged():
    report = cs.fuse_concealment_report((), cs.DEFAULT_CONTAINERS)
    assert report.worst is not None
    assert "royal_egg" in report.flagged
    entries_by_name = {e.name: e for e in report.entries}
    assert entries_by_name["royal_egg"].kind == "mass"


def test_fuse_report_empty():
    report = cs.fuse_concealment_report((), ())
    assert report.entries == () and report.flagged == () and report.worst is None


def test_fuse_report_radiation_kind():
    from octopussy.concealment_sweep import Hotspot

    report = cs.fuse_concealment_report((Hotspot((1.0, 2.0), 5.0),), ())
    assert report.worst is not None
    assert report.worst.kind == "radiation"
    assert report.worst.name == "hotspot@1,2"


def test_catalog_invariants():
    assert cs.CATALOG_SIZE == len(cs._catalog) == 6
    assert "egg" in cs.CATALOG_CATEGORIES
