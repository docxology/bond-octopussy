# Octopussy: FABERGÉ — Special-Agent Mission Software

A BOND-suite film package (film *Octopussy*, 1983; mission codename
**FABERGÉ**). This package implements six investigative disciplines as pure,
deterministic, protocol-conformant modules and exposes them behind the frozen
[BOND-API](../bond-api/) `MissionProvider` contract.

## What it does

- **Artifact forgery detection** (`src/octopussy/forgery_detection.py`) —
  spectral/UV fingerprinting. A ridge-regularized non-negative least-squares
  fit reconstructs each object's pigment composition; anachronistic pigment
  chemistry, UV-varnish fluorescence, and unexplained spectral residue
  jointly yield a *genuine / likely_genuine / likely_forged / forged*
  disposition.
- **Varnish-ageing kinetics** (`src/octopussy/varnish_ageing.py`) — dates a
  painted surface from its yellowing (Beer–Lambert through a growing absorbing
  layer), inverting the model by golden-section to reject freshly varnished
  forgeries by their too-young surface.
- **Circus-cover smuggling logistics** (`src/octopussy/cover_logistics.py`) —
  minimum-cost flow over a rail corridor (successive shortest paths), plus
  circus-train packing, so the payload rides under cover within capacity and
  deadline.
- **Rolling-stock circulation** (`src/octopussy/rolling_stock.py`) — how many
  circus trainsets a schedule needs (Hopcroft–Karp maximum matching / minimum
  path cover), decomposed into itineraries, plus Kuhn–Munkres depot
  allocation.
- **Concealed-device sweep** (`src/octopussy/concealment_sweep.py`) — radiation
  anomaly detection (Poisson background, median-filtered z-score hotspots)
  fused with shape/mass anomaly screening of cargo manifests.
- **Radiation source localization** (`src/octopussy/source_locator.py`) —
  weighted Gauss–Newton nonlinear least squares recovers the concealed
  emitter's position and intensity from the sweep, with approximate
  uncertainty.

The [`src/octopussy/mission.py`](src/octopussy/mission.py) adapter binds the
six modules to the frozen BOND-API protocol and registers their entry points
as gadgets (via a `register_gadgets` hook). Domain modules are
infrastructure-free and importable standalone.

## Directory layout

```
src/octopussy/              domain core + mission adapter + figures + manuscript vars
  forgery_detection.py     spectral/UV forgery fingerprinting
  varnish_ageing.py        varnish yellowing kinetics + age dating
  cover_logistics.py       min-cost flow logistics
  rolling_stock.py         trainset circulation (matching + assignment)
  concealment_sweep.py     radiation + shape/mass anomaly sweep
  source_locator.py        Gauss–Newton source localization
  mission.py               MissionProvider (frozen bond_api protocol) + gadgets
  manuscript_variables.py  {{TOKEN}} hydration
  figures/                 deterministic PNG generation
scripts/                thin CLIs per mission phase (brief/recon/plan/execute/debrief)
manuscript/             numbered sections + config + bib
tests/                  real-data tests, no mocks
```

## Quick start

From this directory:

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/demo_mission.py
uv run python scripts/mission_execute.py    # writes output/data + figures
uv run python scripts/z_generate_manuscript_variables.py
```

The orchestrator discovers this film by slug via `bond_api.load_provider('octopussy')`.

## Gates

- `pytest --cov=src --cov-fail-under=90` — live count/coverage in
  [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md)
- `ruff check` + `ruff format` and `mypy` clean on `src/` and `scripts/`
- no mocks; deterministic fixed-seed computation only

Happy hunting. 🥚
