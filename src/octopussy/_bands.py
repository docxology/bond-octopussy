"""Shared UV-VIS band grid for the FABERGÉ channels.

Both optical channels — the pigment screen (:mod:`octopussy.forgery_detection`)
and the varnish-ageing kinetics (:mod:`octopussy.varnish_ageing`) — sample the
same spectrophotometer band grid. They *must* be the same array, because the
mission multiplies an exhibit spectrum (on the forgery module's grid) by a
varnish transmittance (on the varnish module's grid) band for band and divides
it back out again.

This module is the single definition, so a divergence cannot silently produce
meaningless numbers. It is deliberately not a "domain module": it holds no
logic, only the shared constants, so the rule that no domain module imports
another is not violated — both import this neutral fixture.

Pure stdlib + numpy; no ``infrastructure``, no ``bond_api``.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "BAND_COUNT",
    "BAND_MAX_NM",
    "BAND_MIN_NM",
    "WAVELENGTH_BANDS",
]

#: Spectrophotometer band-grid limits (nm).
BAND_MIN_NM: float = 320.0
BAND_MAX_NM: float = 760.0
BAND_COUNT: int = 24

#: Wavelength grid (nm) of the UV-VIS spectrophotometer, 320-760 nm.
#: The one definition both optical channels sample.
WAVELENGTH_BANDS: np.ndarray = np.linspace(BAND_MIN_NM, BAND_MAX_NM, BAND_COUNT, dtype=float)
