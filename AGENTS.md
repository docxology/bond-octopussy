# AGENTS.md — Octopussy: FABERGÉ

This is a BOND-suite film package inside `projects/working/bond/octopussy/`.
It is a local-only working tree: **no remote, never push**. Scope is exactly
this directory.

## Build and test

```bash
uv sync --extra dev          # required first: bond-api resolves by local path
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Every gate, in the order to run them:

| # | Gate | Command |
|---|---|---|
| 1 | Tests + branch coverage ≥90% on `src/` | `uv run pytest tests/ --cov=src --cov-fail-under=90` |
| 2 | Lint | `uv run ruff check src/ scripts/ tests/` |
| 3 | Format | `uv run ruff format --check src/ scripts/ tests/` |
| 4 | Types | `uv run mypy src/ scripts/` |
| 5 | Manuscript resolves with no unresolved token | `uv run python scripts/z_generate_manuscript_variables.py` |
| 6 | No exemplar leftovers | `rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'` |
| 7 | Clean tree after a path-scoped commit | `git status --short` |

Useful subsets:

```bash
uv run pytest tests/test_mission.py -q            # protocol conformance only
uv run pytest tests/ -q -k manuscript             # the token + bibliography gates
uv run python scripts/demo_mission.py             # full five-stage lifecycle
uv run python scripts/mission_execute.py          # outcome JSON + figures
```

`uv` cannot write its cache under a restrictive sandbox. `Failed to initialize
cache` is an environment restriction, not a package failure — re-run with the
sandbox disabled.

## Layer contract

| Surface | Rule |
|---|---|
| `src/octopussy/forgery_detection.py`, `varnish_ageing.py`, `cover_logistics.py`, `rolling_stock.py`, `concealment_sweep.py`, `source_locator.py` | Pure domain logic — no `infrastructure`, no `bond_api`; importable standalone (stdlib + numpy). Asserted by `tests/test_mission.py::test_mission_uses_no_infrastructure_imports`. |
| `src/octopussy/mission.py` | The single thin adapter importing the frozen `bond_api` protocol. Exposes `MissionProvider` (discovery contract), the module-level `gadget_registry`, and the `register_gadgets` hook. |
| `src/octopussy/manuscript_variables.py`, `figures/` | Protocol-adjacent helpers; may import `mission` and the domain modules. |
| `scripts/` | Thin orchestrators — path building, serialization, printing. No business logic. |
| `tests/` | Real computation only; no mock framework. |

Enforced by the BOND shared guardrails: ≥90% line+branch coverage on `src/`,
zero mock frameworks, deterministic fixed-seed computation, manuscript metrics
injected via `manuscript_variables.py` (never hand-authored), and zero
`template_code_project` strings outside lineage notes.

## Key concepts

- **FABERGÉ** answers three investigative questions with **six** pipelines —
  each question gets a headline detector and an independent confirmer, so a
  verdict never rests on one method's failure mode. `mission.PIPELINES` is the
  authoritative list; `run_faberge` checks its own result keys against it.
- **Authenticity**: `forgery_detection` reads pigment chemistry (ridge NNLS
  unmixing + matched-filter anachronism + UV fluorescence); `varnish_ageing`
  independently dates the surface film by Beer–Lambert yellowing kinetics.
- **Cover**: `cover_logistics` solves min-cost flow over the rail corridor by
  successive shortest paths; `rolling_stock` bounds the trainsets the schedule
  actually needs by maximum bipartite matching (minimum path cover), with
  Kuhn–Munkres depot allocation.
- **Concealment**: `concealment_sweep` fuses a Poisson radiation z-score map
  with per-category mass/density anomaly; `source_locator` turns the resulting
  alarm into a position by weighted Gauss–Newton, reporting its own
  uncertainty.
- Seed is fixed at `mission.SEED == 7`; the three inverse solvers take no
  random draws at all.

## Protocol integration

`bond-api` is a local path dependency (`[tool.uv.sources]`). Run
`uv sync --extra dev` before `pytest`. The orchestrator discovers this film by
importing `octopussy.mission` and instantiating `MissionProvider`;
`bond_api.load_provider('octopussy')` is the supported entry point.

**The protocol surface is frozen.** `brief` / `recon` / `plan` / `execute` /
`debrief`, `gadget_registry`, and `register_gadgets` are consumed by bond-cli,
the coordinator, and the orchestrator across packages. Deepen inside the
package; do not change the shape.

## Development workflow

1. Edit a pure domain module, the mission adapter, or a script.
2. Add or adjust real-data tests; keep zero mocks and make sure the new
   assertion is capable of failing (see `docs/testing_philosophy.md`).
3. If a number reaches the manuscript, add it to `manuscript_variables.py` and
   reference the token from a section — an unreferenced token fails the suite.
4. Run gates 1–6 above.
5. Update `README.md`, `docs/architecture.md`, and
   `docs/testing_philosophy.md` in the same commit when modules change.
6. Path-scoped commit inside this repo only (`git add -A` here, never above).

Full detail: [`docs/agent_instructions.md`](docs/agent_instructions.md) and
[`docs/testing_philosophy.md`](docs/testing_philosophy.md).
