"""Varnish-ageing saturation figure: recovered age scatter vs true age.

Shows the honest limitation the results section carries: the yellowing kinetics
saturate past roughly ``3 tau``, so the recovered age of an old surface
scatters far wider than its young equivalent. A single incident surface of each
true age is re-observed ``trials`` times under independent measurement noise and
re-dated each time (:func:`octopussy.varnish_ageing.age_recovery_scatter`), and
the mean recovered age and its standard deviation are plotted against the true
age. It is indistinguishable from a myth only where the curve breaks down.

Fully deterministic: a fixed seed, a fixed unvarnished reference substrate, and
no wall-clock orderings, so regenerating yields a byte-identical PNG.
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

import numpy as np

from octopussy.forgery_detection import mix_spectrum
from octopussy.varnish_ageing import DEFAULT_TAU_YEARS, age_recovery_scatter

#: Fixed seed for the noise draws, matching the mission's determinism.
_SEED = 7
#: An unvarnished period substrate the examiner could reference.
_REFERENCE = mix_spectrum((("lead_white", 0.4), ("lapis_lazuli", 0.35), ("vermilion", 0.25)))
#: True ages (years) sampled, out past saturation.
_TRUE_AGES = np.arange(5, 401, 15, dtype=float)
#: Noise realizations per true age.
_TRIALS = 24


def plot_varnish_scatter(path: str | Path) -> None:
    """Render the recovered-age-vs-true-age scatter plot to ``path``."""
    matplotlib.use("Agg", force=True)
    rng = np.random.default_rng(_SEED)

    means = np.empty(len(_TRUE_AGES), dtype=float)
    stds = np.empty(len(_TRUE_AGES), dtype=float)
    for index, age in enumerate(_TRUE_AGES):
        scatter = age_recovery_scatter(_REFERENCE, float(age), rng=rng, trials=_TRIALS)
        means[index] = float(scatter.mean_age)
        stds[index] = float(scatter.std_age)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(_TRUE_AGES, _TRUE_AGES, "--", color="#90a4ae", lw=1.2, label="perfect recovery")
    ax.plot(_TRUE_AGES, means, color="#1565c0", lw=2, label="mean recovered age")
    ax.fill_between(
        _TRUE_AGES,
        means - stds,
        means + stds,
        color="#1565c0",
        alpha=0.25,
        label="mean ± 1 std",
    )
    saturation = 3.0 * DEFAULT_TAU_YEARS
    ax.axvline(saturation, color="#c62828", lw=1.2, ls=":", label=f"3 × τ ({saturation:.0f} y)")
    ax.set_xlabel("true varnish age (years)")
    ax.set_ylabel("recovered age (years)")
    ax.set_title("Varnish-ageing recovery: precision collapses at saturation")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
