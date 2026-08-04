"""Concealment sweep figure: radiation count heatmap with detected hotspots."""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

from octopussy.concealment_sweep import (
    RadiationSource,
    SweepGrid,
    anomaly_map,
    detect_hotspots,
    estimate_background,
    simulate_sweep,
)

#: The canonical mission sweep scenario (mirrors ``mission.py``).
_GRID = SweepGrid((0.0, 0.0), 2.0, 10, 10)
_BACKGROUND = 40.0
_SOURCE = RadiationSource((7.0, 7.0), 800.0)
_SEED = 7


def plot_sweep_heatmap(path: str | Path) -> None:
    """Render the radiation sweep heatmap with hotspot markers to ``path``."""
    matplotlib.use("Agg", force=True)
    positions, counts = simulate_sweep(_GRID, _BACKGROUND, (_SOURCE,), seed=_SEED)
    background = estimate_background(counts)
    anomaly = anomaly_map(counts, background)
    hits = detect_hotspots(counts, anomaly, 3.0)

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(counts, origin="lower", aspect="auto", cmap="inferno")
    fig.colorbar(im, ax=ax, label="count rate (cps)")
    for hit in hits:
        i, j = int(hit.position[0]), int(hit.position[1])
        ax.plot(j, i, "o", color="cyan", ms=10, mec="white", mew=1.2)
    ax.set_title("Concealed-device sweep: radiation count rates")
    ax.set_xlabel("detector column")
    ax.set_ylabel("detector row")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
