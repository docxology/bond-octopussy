---
title: "src: octopussy — FABERGÉ"
type: "source_guide"
version: "0.1.0"
---

# src (octopussy)

Layer contract (see `../AGENTS.md` for the full table):

- **Pure domain core** (six modules): `forgery_detection.py`,
  `varnish_ageing.py`, `cover_logistics.py`, `rolling_stock.py`,
  `concealment_sweep.py`, `source_locator.py` — no `infrastructure`, no
  `bond_api`; stdlib + numpy only. No domain module imports another; where one
  needs a shape from elsewhere (`source_locator` ← detector lattice) it takes a
  structural `Protocol` instead of an import, keeping the core acyclic.
- **Thin adapter**: `mission.py` — the single `bond_api` importer; exposes the
  frozen `MissionProvider`, drives `run_faberge` over `PIPELINES`, and
  registers gadgets.
- **Helpers**: `manuscript_variables.py`, `figures/` — may import `mission` and
  the domain modules.

All modules: full type hints, docstrings, deterministic, no mocks. Any new
public function must be covered by a real-data test and keep the boundaries
above. A new domain module must also be added to `mission.PIPELINES`, to
`register_gadgets`, and to the module tables in `README.md`, `../README.md`,
and `../docs/architecture.md`.
