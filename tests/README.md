# tests — Octopussy: FABERGÉ

Real-data test suite, no mocks. Exercises every domain module, the BOND-API
`MissionProvider`, manuscript token hydration, figure generation, and the
thin CLIs.

| File | Coverage |
|---|---|
| `test_forgery_detection.py` | Pigments, mixing, UV, NNLS unmixing, screening, level calibration. |
| `test_cover_logistics.py` | Network validation, min-cost flow, transfer planning, packing. |
| `test_concealment_sweep.py` | Sweep simulation, background/anomaly, hotspots, mass anomaly, fusion. |
| `test_mission.py` | Protocol conformance, discovery, gadgets, determinism. |
| `test_manuscript_variables.py` | Token hydration + live cross-reference gate. |
| `test_figures.py` | Deterministic PNG generation. |
| `test_scripts_smoke.py` | Subprocess CLI smoke tests. |

Run: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
