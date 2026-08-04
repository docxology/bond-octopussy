"""Rail network figure: the FABERGÉ circus corridor with travel times/flow."""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

from octopussy.cover_logistics import DEFAULT_NETWORK_SEGMENTS, RailNetwork, plan_transfer

#: Deterministic planar layout for the corridor stations.
_LAYOUT: dict[str, tuple[float, float]] = {
    "dover": (0.0, 1.0),
    "boulogne": (1.0, 1.6),
    "calais": (1.0, 0.4),
    "amien": (2.2, 1.0),
    "yard": (2.8, 1.9),
    "paris": (3.4, 0.5),
    "garrison": (4.5, 0.5),
    "monastery": (5.6, 0.5),
}


def plot_rail_network(path: str | Path) -> None:
    """Render the circus rail corridor with the routed flow to ``path``."""
    matplotlib.use("Agg", force=True)
    network = RailNetwork()
    transfer = plan_transfer(network, "dover", "monastery", 3, deadline=400, train_capacity=2)
    flow = {f"{e[0]}->{e[1]}": e[2] for e in transfer.edges_used}

    fig, ax = plt.subplots(figsize=(10, 5))
    for edge in DEFAULT_NETWORK_SEGMENTS:
        x0, y0 = _LAYOUT[edge.origin]
        x1, y1 = _LAYOUT[edge.destination]
        ax.plot([x0, x1], [y0, y1], color="#b0bec5", lw=1.5, zorder=1)
        mid = ((x0 + x1) / 2, (y0 + y1) / 2)
        label = f"{edge.travel_time}"
        if f"{edge.origin}->{edge.destination}" in flow:
            label = f"{label} (x{flow[edge.origin + '->' + edge.destination]})"
        ax.text(
            mid[0],
            mid[1],
            label,
            fontsize=8,
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"),
        )
    for node, (x, y) in _LAYOUT.items():
        color = "#c62828" if node in ("dover", "monastery") else "#1565c0"
        ax.plot(x, y, "o", color=color, ms=14, zorder=3)
        ax.text(x, y + 0.18, node, ha="center", fontsize=9, fontweight="bold")
    ax.set_title("FABERGÉ circus rail corridor (minutes; ×flow)")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.5, 6.2)
    ax.set_ylim(-0.2, 2.4)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
