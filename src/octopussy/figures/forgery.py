"""Spectral / UV fingerprint figure: genuine vs forged reflectance + UV bars."""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

from octopussy.forgery_detection import (
    DEFAULT_EXHIBIT,
    WAVELENGTH_BANDS,
    build_uv_response,
    mix_spectrum,
)


def plot_forgery_fingerprints(path: str | Path) -> None:
    """Render the forgery fingerprint figure (spectra + UV response) to ``path``."""
    matplotlib.use("Agg", force=True)
    genuine = mix_spectrum(DEFAULT_EXHIBIT[0].mixture)
    forged = mix_spectrum(DEFAULT_EXHIBIT[2].mixture)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(WAVELENGTH_BANDS, genuine, color="#2e7d32", label="genuine (tsar_egg)")
    ax1.plot(WAVELENGTH_BANDS, forged, color="#c62828", label="forged (modern pigments)")
    ax1.set_xlabel("wavelength (nm)")
    ax1.set_ylabel("reflectance")
    ax1.set_title("Spectral fingerprints")
    ax1.legend()
    ax1.grid(alpha=0.3)

    names = [a.name for a in DEFAULT_EXHIBIT]
    uvs = [build_uv_response(a.mixture) for a in DEFAULT_EXHIBIT]
    colors = ["#2e7d32", "#2e7d32", "#c62828", "#c62828"]
    ax2.bar(names, uvs, color=colors)
    ax2.set_ylabel("UV fluorescence")
    ax2.set_title("UV response by artifact")
    ax2.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
