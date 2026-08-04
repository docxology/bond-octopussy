"""Tests for :mod:`octopussy.figures` (deterministic PNG generation)."""

from __future__ import annotations

from octopussy.figures import FIGURES, generate_all, plot_forgery_fingerprints, plot_rail_network, plot_sweep_heatmap


def test_figure_registry_is_sorted_names():
    assert FIGURES == ("forgery_fingerprints.png", "rail_network.png", "sweep_heatmap.png")


def test_generate_all_writes_all_figures(tmp_path):
    paths = generate_all(tmp_path)
    assert len(paths) == 3
    for path in paths:
        assert path.endswith(".png")


def test_each_figure_is_non_empty(tmp_path):
    plot_forgery_fingerprints(str(tmp_path / "a.png"))
    plot_rail_network(str(tmp_path / "b.png"))
    plot_sweep_heatmap(str(tmp_path / "c.png"))
    for name in ("a.png", "b.png", "c.png"):
        data = (tmp_path / name).read_bytes()
        assert len(data) > 1000
        assert data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic
