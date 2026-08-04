# Agent instructions — Octopussy: FABERGÉ

Operational constraints for agents working inside this BOND film package.
This project is **local-only**: no remote, never push. Scope = this directory.

## Hard rules

1. **Scope**: modify only `projects/working/bond/octopussy/`. Never touch
   sibling packages, bond root files, or the template repo.
2. **Domain purity**: `forgery_detection.py`, `cover_logistics.py`, and
   `concealment_sweep.py` are pure — no `infrastructure` and no `bond_api`
   imports. `mission.py` is the only module that may import `bond_api`.
3. **No mocks**: real data + computation only. Deterministic reference
   providers implement the real protocol.
4. **Determinism**: fixed seed (7); no global RNG; no wall-clock in persisted
   artifacts. Every random draw comes from `numpy.random.default_rng(seed)`.
5. **≥90% line+branch coverage** on `src/`:
   `uv run pytest tests/ --cov=src --cov-fail-under=90`.
6. **Manuscript metrics flow through `manuscript_variables.py`** — never
   hand-author measured numbers in prose.
7. **Gates**: `ruff check` + `ruff format` and `mypy` clean on `src/` and
   `scripts/`; `rg "template[_]code_project"` → zero; `git status` clean after
   a path-scoped commit (`git add -A` inside this repo only).

## Protocol integration

BOND-API is a local path dependency. Run `uv sync --extra dev` before pytest.
Discovery: import `octopussy.mission`, instantiate `MissionProvider` (film
`octopussy`, codename `FABERGÉ`). Register any new gadgets with the suite
`GadgetRegistry` in `mission.py`.

## Verification checklist (before declaring done)

- [ ] `uv run pytest tests/ --cov=src --cov-fail-under=90` passes
- [ ] `uv run ruff check src/ scripts/ tests/` and `ruff format` clean
- [ ] `uv run mypy src/ scripts/` clean
- [ ] `rg -n "template[_]code_project"` → zero
- [ ] `git status` clean after commit
- [ ] report modules + concepts, coverage %, commit SHA

## Common commands

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/demo_mission.py
uv run python scripts/mission_execute.py
uv run python scripts/z_generate_manuscript_variables.py
```
