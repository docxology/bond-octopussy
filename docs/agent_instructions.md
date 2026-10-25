# Agent instructions — Octopussy: FABERGÉ

Operational constraints for agents working inside this BOND film package:
`bond-octopussy`, upstream <https://github.com/docxology/bond-octopussy>
(default branch `main`). Scope = this directory.

## Hard rules

1. **Scope.** Modify only this repository. Never touch a sibling BOND package
   or the template repo. `git add -A` only inside this repo.

2. **Layer purity.** The six domain modules — `forgery_detection.py`,
   `varnish_ageing.py`, `cover_logistics.py`, `rolling_stock.py`,
   `concealment_sweep.py`, `source_locator.py` — are pure: **no
   `infrastructure` imports, no `bond_api` imports**, stdlib + numpy only.
   `mission.py` is the *only* module permitted to import `bond_api`. This is
   not a convention: `tests/test_mission.py::test_mission_uses_no_infrastructure_imports`
   reads each module's source and asserts it.

3. **The protocol surface is frozen.** `mission.py` must keep exposing
   `MissionProvider` with `brief` / `recon` / `plan` / `execute` / `debrief`,
   the module-level `gadget_registry`, and the `register_gadgets` hook — the
   CLI, coordinator, and orchestrator consume them across packages. Deepen
   *inside* the package (new domain modules, richer mission internals); adding
   a public constant is fine, changing or removing a protocol method is not.

4. **No mocks.** Real data + real computation only. No `MagicMock`, no
   `mocker.patch`, no `unittest.mock`. Where a test needs a variant scenario,
   pass it in as data (every domain entry point takes its library, catalog,
   exhibit, or network as an argument) rather than replacing a dependency.

5. **Determinism.** Fixed seed (`mission.SEED == 7`); no global RNG; no
   wall-clock value in a persisted artifact. Every random draw comes from a
   caller-supplied `numpy.random.default_rng(seed)`. The three inverse solvers
   (golden-section, Hopcroft–Karp, Gauss–Newton) take no random draws at all.

6. **≥90% line+branch coverage** on `src/`:
   `uv run pytest tests/ --cov=src --cov-fail-under=90`.

7. **Manuscript metrics flow through `manuscript_variables.py`.** Never
   hand-author a measured number in prose. Three tests enforce this in both
   directions — no section may use a token the generator does not emit, no
   generated token may go unreferenced, and no bare numeral may appear in
   abstract/results/conclusion prose.

8. **No leftover exemplar identifiers.** `rg "template[_]code_project"` → zero
   outside docs that explicitly explain the exemplar lineage.

## Where things live

| You want to change… | Edit |
|---|---|
| An algorithm | the relevant pure module in `src/octopussy/` |
| What the mission runs or reports | `src/octopussy/mission.py` (`run_faberge`, `PIPELINES`) |
| A number that appears in the manuscript | `src/octopussy/manuscript_variables.py`, then reference the token |
| A figure | `src/octopussy/figures/` (never the PNG) |
| A CLI's I/O or printing | `scripts/` — orchestration only, no business logic |

## Protocol integration

`bond-api` is a local path dependency (`[tool.uv.sources]` in
`pyproject.toml`). Run `uv sync --extra dev` before pytest. Discovery: the
orchestrator imports `octopussy.mission` and instantiates `MissionProvider`
(film `octopussy`, codename `FABERGÉ`); `bond_api.load_provider('octopussy')`
is the supported entry point. Register any new gadget inside
`register_gadgets()` so both the module registry and a caller-supplied
registry receive it.

## Adding a new domain module

1. Write it pure (stdlib + numpy), fully typed, docstringed, deterministic.
2. Add a `tests/test_<module>.py` covering the happy path, the edge cases, and
   every `raise` — see [`testing_philosophy.md`](testing_philosophy.md).
3. Wire it into `run_faberge` and append its key to `mission.PIPELINES`.
4. Register its entry point as a gadget in `register_gadgets()`.
5. Add its outputs as tokens in `manuscript_variables.py` **and** reference
   every one of them from a manuscript section (an unreferenced token fails).
6. Update `docs/architecture.md`, `docs/testing_philosophy.md`, `README.md`,
   and `AGENTS.md` in the same commit.

## Verification checklist (before declaring done)

- [ ] `uv run pytest tests/ --cov=src --cov-fail-under=90` — 0 failures, 0 skips
- [ ] `uv run ruff check src/ scripts/ tests/` and `uv run ruff format --check src/ scripts/ tests/`
- [ ] `uv run mypy src/ scripts/` clean
- [ ] `rg -n "template[_]code_project"` → zero (outside lineage notes)
- [ ] `uv run python scripts/z_generate_manuscript_variables.py` exits 0 with no unresolved token
- [ ] `git status` clean after a path-scoped commit
- [ ] report modules touched, measured coverage %, and commit SHA

## Common commands

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/demo_mission.py                    # full five-stage lifecycle
uv run python scripts/mission_execute.py                 # outcome JSON + figures
uv run python scripts/z_generate_manuscript_variables.py # tokens + resolved manuscript
```

`uv` cannot write its cache under a restrictive sandbox. A
`Failed to initialize cache` error is an environment restriction, not a
package failure — re-run with the sandbox disabled.
