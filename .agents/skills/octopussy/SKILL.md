---
name: octopussy
description: Use when working inside the Octopussy: FABERGÉ BOND film package (forgery detection, cover logistics, concealment sweep / MissionProvider).
version: 1.0.0
tags: [bond, faberge, forgery-detection, min-cost-flow, mission-provider]
---

# octopussy

Build/maintain the **Octopussy: FABERGÉ** BOND film package in this repository
(`bond-octopussy`, upstream <https://github.com/docxology/bond-octopussy>,
default branch `main`). Scope = this directory only.

## When to use

- Editing the forgery / logistics / concealment domain modules.
- Maintaining the `MissionProvider` (frozen `bond_api` protocol) or its gadgets.
- Regenerating figures, manuscript variables, or mission artifacts.
- Verifying the package against the BOND guardrails.

## Quick reference

```bash
uv sync --extra dev            # bond-api is a local path dependency
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/demo_mission.py
uv run python scripts/z_generate_manuscript_variables.py
```

Discovery: `bond_api.load_provider('octopussy', search_paths=['src'])`
imports `octopussy.mission.MissionProvider`.

## Modules

Six pure domain modules, paired one headline detector + one depth module per
investigative problem:

- `src/octopussy/forgery_detection.py` — spectral/UV forgery screen (ridge
  NNLS unmixing + UV fluorescence + matched-filter anachronism).
- `src/octopussy/varnish_ageing.py` — Beer–Lambert varnish yellowing kinetics;
  dates a surface by bounded golden-section search.
- `src/octopussy/cover_logistics.py` — min-cost flow (successive shortest
  paths), golden-ticket Dijkstra, circus-train packing.
- `src/octopussy/rolling_stock.py` — Hopcroft–Karp trainset circulation +
  Kuhn–Munkres depot allocation.
- `src/octopussy/concealment_sweep.py` — radiation anomaly + shape/mass
  anomaly fusion.
- `src/octopussy/source_locator.py` — damped Gauss–Newton emitter localization.
- `src/octopussy/mission.py` — thin `bond_api` adapter + gadget registry;
  `manuscript_variables.py` and `figures/` sit beside it.

## Pitfalls

- **Domain purity**: the six domain modules must stay free of
  `infrastructure` and `bond_api` imports (mission.py is the only importer).
- **Determinism**: all RNG via `numpy.random.default_rng(seed)` with seed 7;
  no wall-clock in persisted artifacts.
- **No mocks**: real computation in tests only.
- **Manuscript tokens**: never hand-author metrics in prose; add tokens to
  `manuscript_variables.py` and let the cross-reference test gate them.
- **Deep-path E402**: script `sys.path` bootstrap imports need `# noqa: E402`.

## Verify before done

1. pytest gate ≥90% coverage (live count in `docs/_generated/COUNTS.md`)
2. ruff check + format, mypy clean
3. `rg "template[_]code_project"` → zero
4. `git status` clean after a path-scoped commit (`git add -A` here only)
