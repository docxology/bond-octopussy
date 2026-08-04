---
title: "src: octopussy — FABERGÉ"
type: "source_guide"
version: "0.1.0"
---

# src (octopussy)

Layer contract (see `../AGENTS.md` for the full table):

- **Pure domain core**: `forgery_detection.py`, `cover_logistics.py`,
  `concealment_sweep.py` — no `infrastructure`, no `bond_api`; stdlib + numpy.
- **Thin adapter**: `mission.py` — imports `bond_api`, exposes `MissionProvider`
  and registers gadgets.
- **Helpers**: `manuscript_variables.py`, `figures/` — may import `mission` and
  domain modules.

All modules: full type hints, docstrings, deterministic, no mocks. Any new
public function must be covered by a real-data test and keep the boundaries
above.
