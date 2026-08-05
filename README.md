# Octopussy: FABERGÉ — Special-Agent Mission Software

A BOND-suite film package (film *Octopussy*, 1983; mission codename
**FABERGÉ**). It implements the film's investigative problems as six pure,
deterministic algorithm modules and exposes them behind the frozen
[BOND-API](../bond-api/) `MissionProvider` contract.

## From film to software

*Octopussy* turns on three problems, and the package implements each one
twice — a headline detector plus a depth module reading a different observable
of the same scenario. The pairing buys independence of *observable*, not of
sample, and a second observable only confirms anything to the extent its own
uncertainty has been measured. It has been: the varnish channel decisively
rejects a freshly re-varnished surface and returns only a *failure to reject*
on a century-old one, because the yellowing kinetics saturate. See the results
section of the manuscript for the measured scatter.

| In the film | The problem | Headline module | Depth module |
|---|---|---|---|
| A Fabergé egg is switched for a forgery at auction | Is this object what it claims to be? | `forgery_detection` | `varnish_ageing` |
| A circus train carries the payload across Europe under cover | Can the cargo move, and can the cover be flown? | `cover_logistics` | `rolling_stock` |
| A nuclear device hides inside an ordinary-looking prop | Is something hidden here — and where exactly? | `concealment_sweep` | `source_locator` |

## Modules

Everything under `src/octopussy/`, one line each:

| Module | What it computes |
|---|---|
| `forgery_detection.py` | Spectral/UV fingerprinting: ridge-regularized non-negative least-squares unmixing of a reflectance spectrum against a pigment library, fused with matched-filter anachronism evidence and a UV fluorescence reading, into a genuine / likely_genuine / likely_forged / forged disposition. |
| `varnish_ageing.py` | Varnish yellowing kinetics: Beer–Lambert transmittance through a saturating-exponential absorbing layer, inverted by bounded golden-section search to date a surface and judge it against the claimed provenance. |
| `cover_logistics.py` | Minimum-cost flow over the circus rail corridor by successive shortest paths (Bellman–Ford augmenting paths), plus per-unit route decomposition for a makespan, deadline slack, Dijkstra single-courier routing, and circus-train packing. |
| `rolling_stock.py` | Trainset circulation: Hopcroft–Karp maximum bipartite matching over trip-successor compatibility gives the minimum fleet by minimum path cover, decomposed into itineraries, with Kuhn–Munkres depot allocation. |
| `concealment_sweep.py` | Concealed-device sweep: seeded Poisson detector simulation, median-filtered background, Poisson-normalized z-score anomaly map and local-maximum hotspots, fused with per-category shape/mass anomaly screening of a cargo manifest. |
| `source_locator.py` | Radiation source localization: damped Gauss–Newton weighted nonlinear least squares recovers the emitter's position and intensity from the sweep, with approximate positional uncertainty from the inverse normal matrix. |
| `mission.py` | The single `bond_api` seam — the `MissionProvider` implementation, the six-pipeline `run_faberge` driver, provenance, and the gadget registry. |
| `manuscript_variables.py` | Hydrates every manuscript token from `manuscript/config.yaml` plus a live mission run, and resolves the manuscript tree in strict mode. |
| `figures/` | Deterministic matplotlib figure generation (Agg backend). |

The six domain modules are pure — stdlib and numpy only, no `bond_api`, no
`infrastructure` — and importable standalone. That boundary is asserted by a
test, not merely documented.

## The MissionProvider surface

`src/octopussy/mission.py` supplies the structural contract the coordinator,
orchestrator, and CLI consume across all BOND packages. **This shape is
frozen.**

```python
from bond_api import load_provider
from bond_api.protocol import ReconRequest, run_mission

provider = load_provider("octopussy")   # film slug -> MissionProvider
debrief  = run_mission(provider, ReconRequest("sweep the exhibition hall"))
```

| Member | Signature | Returns |
|---|---|---|
| `film` | attribute | `"octopussy"` |
| `brief` | `() -> MissionBrief` | Codename `FABERGÉ`, three objectives, three scenario assets, two constraints. |
| `recon` | `(ReconRequest) -> ReconReport` | Findings describing the goal and the scenario inventory. |
| `plan` | `(MissionBrief) -> MissionPlan` | One step per pipeline plus a verification step. |
| `execute` | `(MissionPlan) -> MissionOutcome` | Runs all six pipelines; results dict plus `Provenance` (version, seed, sha256 input hash). |
| `debrief` | `(MissionOutcome) -> Debrief` | The outcome plus standing lessons. |

Alongside it: the module-level `gadget_registry` and the
`register_gadgets(registry=None)` hook, carrying six gadgets — `forge_screen`,
`route_cargo`, `sweep_concealment`, `varnish_age`, `circulate_fleet`,
`locate_source`. Adding a public constant is fine; changing or removing any of
the above breaks cross-package discovery.

## Directory layout

```
src/octopussy/          domain core + mission adapter + figures + manuscript vars
scripts/                thin CLIs per mission phase (brief/recon/plan/execute/debrief)
manuscript/             numbered sections + config.yaml + references.bib
tests/                  real-data tests, no mocks
docs/                   architecture, agent instructions, testing doctrine
output/                 disposable, regenerated (outcome JSON, figures, resolved manuscript)
```

## Quick start

From this directory:

```bash
uv sync --extra dev                                       # resolves bond-api by local path
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/demo_mission.py                     # full five-stage lifecycle
uv run python scripts/mission_execute.py                  # -> output/data + output/figures
uv run python scripts/z_generate_manuscript_variables.py  # -> output/manuscript
```

`uv` cannot write its cache under a restrictive sandbox; a
`Failed to initialize cache` error is an environment restriction, not a
package failure.

## Gates

| Gate | Command |
|---|---|
| Tests + branch coverage ≥90% on `src/` | `uv run pytest tests/ --cov=src --cov-fail-under=90` |
| Lint + format | `uv run ruff check src/ scripts/ tests/` · `uv run ruff format --check src/ scripts/ tests/` |
| Types | `uv run mypy src/ scripts/` |
| No exemplar leftovers | `rg -n "template[_]code_project"` → zero outside lineage notes |

No mocks anywhere; every pipeline is deterministic under a fixed seed. The
currently measured test count and coverage percentage live in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) — regenerated from a
real run rather than quoted in prose here, so this file cannot go stale.

## Docs

- [`docs/agent_instructions.md`](docs/agent_instructions.md) — rules and verification checklist
- [`docs/architecture.md`](docs/architecture.md) — module-by-module architecture
- [`docs/testing_philosophy.md`](docs/testing_philosophy.md) — no-mock / determinism doctrine
- [`AGENTS.md`](AGENTS.md) — build/test/verify reference
- [`TODO.md`](TODO.md) — remaining work

This package was forked from the template exemplar `template_code_project`;
that lineage is why the pipeline, manuscript, and gate conventions look like
the template's. Nothing of the exemplar's own domain remains.

Happy hunting. 🥚
