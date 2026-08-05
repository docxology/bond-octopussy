# octopussy TODO

Forward-only backlog for the FABERGÉ film package (BOND suite, phase 2).

## Built (phase 2 — FABERGÉ)

- **Domain core** (`src/octopussy/`, pure, infrastructure-free):
  - `forgery_detection.py` — spectral/UV forgery fingerprinting: ridge NNLS
    unmixing, matched-filter anachronism evidence, UV fluorescence, residual —
    yields genuine/likely_genuine/likely_forged/forged dispositions.
  - `cover_logistics.py` — circus-cover smuggling logistics: min-cost flow by
    successive shortest paths over a rail corridor; golden-ticket Dijkstra;
    circus-train packing; deadline-aware transfer planning.
  - `concealment_sweep.py` — concealed-device sweep: seeded Poisson radiation
    simulation, median-filter background, z-score anomaly map, hotspot
    detection; per-category mass/density anomaly; fused prioritized report.
- **Protocol adapter** (`src/octopussy/mission.py`): frozen `bond_api`
  `MissionProvider` (film `octopussy`, codename `FABERGÉ`); registers
  `forge_screen`, `route_cargo`, `sweep_concealment` gadgets; deterministic
  provenance (fixed seed 7, sha256 `input_hash`).
- **Support**: `manuscript_variables.py` ({{TOKEN}} hydration incl. live
  result tokens), deterministic `figures/` (3 PNGs), thin `scripts/` CLIs per
  mission phase (brief/recon/plan/execute/debrief + demo + z_generate).
- **Tests**: 7 files, real-data only, no mocks; live cross-reference gate on
  manuscript tokens; subprocess CLI smoke tests. Live count + coverage →
  `docs/_generated/COUNTS.md`.

## Deepened (phase 4 — FABERGÉ deep improvement)

- **Three new pure domain modules**:
  - `varnish_ageing.py` — Beer–Lambert varnish yellowing kinetics
    (`d(t)=d_max(1−e^{−t/τ})`), bounded golden-section age inversion, claimed-era
    verdict (consistent / too_young / too_old).
  - `rolling_stock.py` — trainset circulation: Hopcroft–Karp max bipartite
    matching → minimum trainsets (min path cover), itinerary chain
    decomposition, and Kuhn–Munkres minimum-cost assignment for depot
    allocation.
  - `source_locator.py` — weighted Gauss–Newton nonlinear least squares
    localization (numerical Jacobian, damped normal equations, excess-centroid
    start, deterministic line search) + approximate uncertainty.
- **Deepened mission internals**: `run_faberge` now drives **six** pipelines
  (forgery, logistics, concealment, varnish, rolling_stock, source_locator);
  plan() carries six steps; three new gadgets registered + a `register_gadgets`
  hook added. Protocol surface (`MissionProvider` brief/recon/plan/execute/
  debrief, `gadget_registry`) unchanged.
- **Manuscript**: methodology/results/conclusion extended with the deepened
  outputs via ~16 new live `{{TOKEN}}`s; references.bib extended with real
  sources (Feller 1994, Horie 2010, Ahuja–Magnanti–Orlin 1993, Caprara et al.
  2002, Hopcroft–Karp 1973, Kuhn 1955, Nocedal & Wright 2006).
- **Tests**: +3 files (test_varnish_ageing, test_rolling_stock,
  test_source_locator), 119 total, no mocks, 0 failures, 0 skipped.

## Declared integration points

- **BOND-API**: consumed via local path dependency (`[tool.uv.sources]`) —
  DONE this phase. Run `uv sync --extra dev` before pytest.
- **bond-utilities provenance**: currently the adapter computes its own
  `input_hash`; when bond-utilities ships, consider delegating provenance
  persistence to `bond_utilities.mission_io.record_provenance_outcome`
  (acceptance: mission outcomes persist through that helper without changing
  the mission results dict). Not blocking — provenance is already emitted.
- **bond-coordinator / orchestrator**: the film is discoverable by slug via
  `bond_api.load_provider('octopussy')`; no orchestration-specific work needed
  until coordinators land.

## Future / hardening

- Widen the pigment library and add explicit negative controls (a genuine
  yellow period piece) before extending the anachronism claim.
- Consider a physical two-detector coincidence model for the sweep.
- Keep figures and manuscript variables regenerated, never hand-maintained.
