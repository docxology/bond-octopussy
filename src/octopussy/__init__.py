"""Octopussy: FABERGÉ — special-agent mission software (BOND film package).

Codename *FABERGÉ*, after the octopus-cover jewel mission of the 1983 film
*Octopussy*. The package implements the mission's three investigative problems,
each as a headline detector paired with a depth module reading a different
observable of the same scenario:

* :mod:`octopussy.forgery_detection` — spectral/UV fingerprinting of painted
  artifacts to expose forgeries (period-anachronistic pigments, modern
  varnish fluorescence, unexplained spectral residue), with
  :mod:`octopussy.varnish_ageing` dating the surface film of the same
  artifacts by Beer-Lambert yellowing kinetics.
* :mod:`octopussy.cover_logistics` — circus-cover smuggling logistics: routing
  and packing payloads over a rail network as min-cost flow, so illicit cargo
  rides the troupe's train under cover, with
  :mod:`octopussy.rolling_stock` bounding the trainsets the schedule needs by
  maximum bipartite matching.
* :mod:`octopussy.concealment_sweep` — concealed-device detection: radiation
  anomaly sweeps fused with shape/mass anomaly screening of cargo manifests,
  with :mod:`octopussy.source_locator` recovering the emitter's position from
  the resulting alarm.

The six domain modules are pure domain logic (stdlib + numpy only) and are
importable without the rest of the BOND suite. The mission adapter
:mod:`octopussy.mission` binds them to the frozen ``bond_api`` protocol.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "__version__",
]
