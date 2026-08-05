# tests — Octopussy: FABERGÉ

Real-data test suite, no mocks. Exercises every domain module, the BOND-API
`MissionProvider`, manuscript token hydration, figure generation, and the
thin CLIs.

| File | Coverage |
|---|---|
| `test_forgery_detection.py` | Pigments, mixing, UV, NNLS unmixing, screening, level calibration. |
| `test_varnish_ageing.py` | Yellowing kinetics, age inversion, era verdicts. |
| `test_cover_logistics.py` | Network validation, min-cost flow (capacity limits, infeasibility, self-transfer rejection), transfer planning, Dijkstra routing, packing. |
| `test_rolling_stock.py` | Trip validation, Hopcroft–Karp matching, chains, Hungarian assignment. |
| `test_concealment_sweep.py` | Sweep simulation and determinism, background/anomaly maps, hotspot thresholding, mass anomaly, fused ranking. |
| `test_source_locator.py` | Gauss–Newton localization, uncertainty, the `DetectorLattice` protocol, sweep wrapper. |
| `test_mission.py` | Protocol conformance, discovery, the `PIPELINES` invariant, derived sweep constants, provenance, gadgets, determinism, layer-purity scan. |
| `test_manuscript_variables.py` | Token hydration, strict tree resolution, and four manuscript gates (token both-ways, bibliography both-ways, no bare numerals, derived-token proofs). |
| `test_figures.py` | Deterministic PNG generation. |
| `test_scripts_smoke.py` | Subprocess CLI smoke tests. |

Run: `uv run pytest tests/ --cov=src --cov-fail-under=90`.

New tests must be capable of failing — see
[`../docs/testing_philosophy.md`](../docs/testing_philosophy.md) for the
anti-vacuity rules (no monotone-trivial assertions, no fields that cannot
vary, non-empty scan sets, reproduce-before-fix).
