# Architecture — Octopussy: FABERGÉ

The package is a thin protocol adapter over **six** pure domain modules. The
domain core knows nothing about the BOND suite; `mission.py` is the single
seam where it meets the frozen `bond_api` protocol.

## Layers

```
 scripts/  (thin CLIs, one per mission phase; I/O and printing only)
    |
    v
 src/octopussy/mission.py       MissionProvider + gadget registry  [imports bond_api]
    |          |
    |          +--> manuscript_variables.py --> manuscript/config.yaml + a live run
    |
    v
 src/octopussy/                 pure domain core  [no bond_api, no infrastructure]
   forgery_detection.py    (numpy)   varnish_ageing.py    (numpy)
   cover_logistics.py      (stdlib)  rolling_stock.py     (stdlib)
   concealment_sweep.py    (numpy)   source_locator.py    (numpy)
    |
    +--> figures/  (deterministic matplotlib PNGs, Agg backend)
```

Dependency direction is strictly downward. No domain module imports another
domain module; `source_locator` consumes a detector lattice through the
structural `DetectorLattice` protocol rather than importing
`concealment_sweep`, which keeps the two decoupled and acyclic.

## The three disciplines, paired

The design commitment is that each discipline is answered twice, by methods
with disjoint failure modes. The headline module raises the alarm; the depth
module tests the same conclusion along an independent route.

| Discipline | Headline | Depth |
|---|---|---|
| Authenticity | `forgery_detection` (pigment chemistry) | `varnish_ageing` (film kinetics) |
| Cover feasibility | `cover_logistics` (can the route carry it?) | `rolling_stock` (do enough trainsets exist?) |
| Concealment | `concealment_sweep` (is something here?) | `source_locator` (where exactly?) |

## Domain modules

### `forgery_detection.py` — spectral/UV fingerprinting
Models a painted artifact as a weighted pigment mixture over a
`WAVELENGTH_BANDS` grid (`BAND_COUNT` bands from `BAND_MIN_NM` to
`BAND_MAX_NM`), drawn from the immutable `PIGMENT_LIBRARY`.
- Forward: `mix_spectrum`, `build_uv_response`, `measure_spectrum`,
  `read_artifact` — produce the noised `SpectrumReading` the detector sees.
  The detector never receives the true mixture.
- Inverse: `_nnls_fit` (ridge-regularized non-negative least squares by
  coordinate descent, unit-normalized columns), `estimate_mixture`.
- Decision: `screen_reading` fuses three channels — anachronism (matched
  filter on the era-restricted residual plus residual improvement), UV
  fluorescence, and unexplained era-consistent residue — into a 0–1 score,
  then `_level_for_score` maps it to a `ForgeryLevel`
  (genuine / likely_genuine / likely_forged / forged).
- Batch: `screen_artifact`, `screen_collection` over `DEFAULT_EXHIBIT`.
- Types: `Pigment`, `Artifact`, `SpectrumReading`, `ForgeryVerdict`.

### `varnish_ageing.py` — yellowing kinetics and surface dating
- Forward: `yellowing_extent` (`d(t) = d_max(1 − e^{−t/τ})`),
  `varnish_transmittance` (Beer–Lambert through the growing absorbing layer),
  `apply_varnish_aging` (age a reflectance spectrum).
- Inverse: `estimate_varnish_age` — bounded golden-section least-squares fit
  over the age axis via `_golden_section_minimize`. Derivative-free and
  start-point-independent, so it is deterministic without a seed.
- Decision: `age_verdict` and `assess_varnish` compare the estimated age with
  the age the claimed provenance implies, returning
  `AgeVerdict` (consistent / too_young / too_old) plus a closeness score.

### `cover_logistics.py` — min-cost flow over the rail corridor
- Graph: `Edge`, `RailNetwork` (validating directed graph; rejects
  self-loops, non-positive travel time, non-positive capacity),
  `DEFAULT_NETWORK_SEGMENTS`.
- Flow: `min_cost_flow` — successive shortest paths, with `_augmenting_path`
  finding residual paths by Bellman–Ford (needed because reverse arcs carry
  negative reduced cost). Raises `LogisticsInfeasibleError` when the corridor
  cannot carry the demand; rejects a source==sink request as a `ValueError`.
- Planning: `plan_transfer` — the non-raising entry point; decomposes flow
  into per-unit routes for a makespan, checks the deadline for slack, and
  packs `pack_circus_trains`. Returns `TransferPlan` with `feasible=False`
  rather than raising when the corridor is short.
- Also: `golden_ticket_route` (single-courier least-cost path by Dijkstra).

### `rolling_stock.py` — trainset circulation
- Model: `Trip` (validated integer schedule), `can_follow`,
  `compatibility_edges` (the trip-successor bipartite graph).
- Matching: `maximum_matching` — Hopcroft–Karp, iterating in index order so
  the returned matching is reproducible.
- Fleet: `minimum_trainsets` (`n − M`, the minimum-path-cover bound) and
  `fleet_circulation`, which decomposes the matching into concrete itinerary
  chains and totals deadhead, returning `FleetPlan`.
- Assignment: `kuhn_munkres` — Hungarian algorithm on a square cost matrix for
  depot allocation.

### `concealment_sweep.py` — radiation + shape/mass anomaly
- Radiation: `SweepGrid` (detector lattice), `RadiationSource`,
  `simulate_sweep` (seeded Poisson draws about background plus inverse-square
  contributions), `estimate_background` (windowed median),
  `anomaly_map` (Poisson-normalized z-score), `detect_hotspots` (8-connected
  local maxima clearing a single `threshold`).
- Mass: `Container`, `mass_anomaly` against a per-category density/tolerance
  catalog (`CATALOG_CATEGORIES`, `CATALOG_SIZE`), yielding `MassAnomaly`.
- Fusion: `fuse_concealment_report` ranks both channels into one
  `ConcealmentReport` of `ConcealmentEntry` rows plus a flagged list.

### `source_locator.py` — weighted Gauss–Newton localization
- Forward: `model_counts`, `weighted_residual`, `excess_counts`.
- Solver: `gauss_newton_source` — numerical central-difference Jacobian,
  damped normal equations, deterministic step-halving line search, and an
  excess-weighted-centroid start (`_initial_guess`) so no random state is
  needed. Returns `SourceEstimate` with convergence diagnostics.
- Precision: `localization_uncertainty` returns approximate `(σx, σy, σI)`
  from the inverse normal matrix, so a fix always ships with its precision.
- Interop: `locate_from_sweep` accepts any `DetectorLattice` — the structural
  protocol that `SweepGrid` satisfies.

## How `mission.py` implements the frozen `MissionProvider`

`bond_api.protocol.MissionProvider` is a `@runtime_checkable` structural
`Protocol` declaring `film: str` plus five stages. `octopussy.mission` supplies
a concrete class of the same name; nothing subclasses the protocol, so
conformance is structural and is asserted at test time with
`isinstance(load_provider('octopussy'), Protocol)`.

| Stage | Signature | What this package does |
|---|---|---|
| `brief` | `() -> MissionBrief` | Declares film `octopussy`, codename `FABERGÉ`, the three headline objectives, three scenario `Asset`s (exhibit size, corridor segments, `SWEEP_DETECTORS`), and two `Constraint`s (determinism, cover capacity). The objective tuple feeds `_input_hash`, so it is held stable across depth work. |
| `recon` | `(ReconRequest) -> ReconReport` | Echoes the goal and reports the scenario inventory as `Finding` rows. Read-only; runs no pipeline. |
| `plan` | `(MissionBrief) -> MissionPlan` | Emits one `Step` per pipeline plus a `verify` step. Note the frozen signature takes the **brief**, not the recon report — `run_mission` deliberately does not thread recon into planning, so a film needing recon evidence must carry it itself. |
| `execute` | `(MissionPlan) -> MissionOutcome` | Calls `run_faberge(SEED)` and wraps the result with `Provenance` (package version, seed, sha256 `input_hash` over codename + objectives + plan steps, `wall_time_s=0.0` so no clock enters a persisted artifact). |
| `debrief` | `(MissionOutcome) -> Debrief` | Returns the outcome plus standing lessons, one family per pipeline. |

`run_faberge` is the real work: it drives all six pipelines in order and
returns a JSON-serializable dict whose top-level keys must equal
`mission.PIPELINES` — a structural invariant checked before the dict is
returned, so the pipeline count in docs and manuscript can never silently
diverge from the code. `PIPELINE_COUNT` is derived from that same tuple.

### Gadgets

`register_gadgets(registry=None)` registers this film's six callable entry
points — `forge_screen`, `route_cargo`, `sweep_concealment`, `varnish_age`,
`circulate_fleet`, `locate_source` — with a `bond_api.registry.GadgetRegistry`.
It is idempotent (re-registering replaces the payload) and defaults to the
module-level `gadget_registry`, which is populated at import time. Both the
hook and the module-level registry are part of the frozen discovery contract.

## Figures and manuscript

`figures/` renders `forgery_fingerprints.png`, `rail_network.png`, and
`sweep_heatmap.png` from the live domain algorithms under the Agg backend;
`generate_all` is the single entry point and `FIGURES` is the canonical name
list. `manuscript_variables.py` hydrates every manuscript token from
`manuscript/config.yaml` plus a live `run_faberge` call, and
`resolve_manuscript_tree` writes the resolved sections to `output/manuscript/`
in strict mode — an unresolved token is a hard failure, never a rendered brace.

## Boundaries (enforced, not aspirational)

- Domain modules import neither `infrastructure` nor `bond_api` — asserted by
  reading their source in `tests/test_mission.py`.
- `mission.py` is the only `bond_api` importer.
- `scripts/` are thin: they build paths, call `src/`, serialize, and print.
- Nothing writes into the repository at import time; all output goes to
  `output/`, which is disposable and regenerated.
