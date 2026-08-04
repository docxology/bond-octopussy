"""FABERGÉ figure generation.

Deterministic matplotlib figures (Agg backend) for the manuscript. Each
generator writes one PNG under ``output/figures/`` and is exercised by
``tests/test_figures.py`` (file exists and is non-empty). No figures are
hand-edited: they are regenerated from the domain algorithms.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg", force=True)

from pathlib import Path

from octopussy.figures.forgery import plot_forgery_fingerprints
from octopussy.figures.logistics import plot_rail_network
from octopussy.figures.sweep import plot_sweep_heatmap

__all__ = ["FIGURES", "generate_all", "plot_forgery_fingerprints", "plot_rail_network", "plot_sweep_heatmap"]

#: Canonical figure filenames (order matches :func:`generate_all`).
FIGURES: tuple[str, ...] = ("forgery_fingerprints.png", "rail_network.png", "sweep_heatmap.png")


def generate_all(output_dir: str | Path) -> list[str]:
    """Render every FABERGÉ figure; return the list of absolute PNG paths."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = [str(output / name) for name in FIGURES]
    plot_forgery_fingerprints(output / "forgery_fingerprints.png")
    plot_rail_network(output / "rail_network.png")
    plot_sweep_heatmap(output / "sweep_heatmap.png")
    return paths
