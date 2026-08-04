# AGENTS.md — Octopussy: FABERGÉ

This is a BOND-suite film package inside `projects/working/bond/octopussy/`.
It is a local-only working tree: **no remote, never push**. Scope is exactly
this directory.

## Layer contract

| Surface | Rule |
|---|---|
| `src/octopussy/forgery_detection.py`, `cover_logistics.py`, `concealment_sweep.py` | Pure domain logic — no `infrastructure`, no `bond_api`; importable standalone (stdlib + numpy). |
| `src/octopussy/mission.py` | The single thin adapter importing the frozen `bond_api` protocol; exposes `MissionProvider` (discovery contract) and registers gadgets. |
| `src/octopussy/manuscript_variables.py`, `figures/` | Protocol-adjacent helpers (may import `mission`/domain). |
| `scripts/` | Thin orchestrators; may import `octopussy` and `bond_api`. |
| `tests/` | Real computation only, no mocks. |

Enforced by the BOND shared guardrails: ≥90% line+branch coverage on `src/`,
`rg "template[_]code_project"` → zero, no mock frameworks, deterministic
fixed-seed computation, manuscript metrics injected via
`manuscript_variables.py` (never hand-authored).

## Key concepts

- **FABERGÉ** mission: three objectives — detect forgeries, route cargo under
  cover, sweep for the concealed device. Seed is fixed (7).
- **Forgery detection**: ridge NNLS spectral unmixing + UV fluorescence +
  matched-filter anachronism evidence.
- **Cover logistics**: min-cost flow by successive shortest paths over a rail
  corridor; circus-train packing.
- **Concealment sweep**: Poisson radiation background + median-filtered
  z-scores, fused with per-category mass/density anomaly scoring.

## Protocol integration

`bond-api` is a local path dependency (`[tool.uv.sources]`). Run
`uv sync --extra dev` before `pytest`. The orchestrator discovers the film by
importing `octopussy.mission` and instantiating `MissionProvider`.

## Development workflow

1. Edit domain modules (pure), mission adapter, or scripts.
2. Add/adjust real-data tests; keep zero mocks.
3. `uv run pytest tests/ --cov=src --cov-fail-under=90`
4. `uv run ruff check src/ scripts/ tests/ && uv run ruff format src/ scripts/ tests/`
5. `uv run mypy src/ scripts/`
6. `rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'`
7. Path-scoped commit inside this repo (`git add -A` here only).

See [`docs/agent_instructions.md`](docs/agent_instructions.md) and
[`docs/testing_philosophy.md`](docs/testing_philosophy.md) for full detail.
