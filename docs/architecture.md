# Architecture — Octopussy: FABERGÉ

The package is a thin protocol adapter over three pure domain modules.

## Layers

```
 scripts/  (thin CLIs, one per mission phase)
    |
    v
 src/octopussy/mission.py          MissionProvider + GadgetRegistry (imports bond_api)
    |          |
    |          +--> manuscript_variables.py ---> manuscript/config.yaml + live run
    v
 src/octopussy/forgery_detection.py   (pure; numpy only)
 src/octopussy/cover_logistics.py     (pure; stdlib only)
 src/octopussy/concealment_sweep.py   (pure; numpy only)
    |
    +--> figures/  (deterministic matplotlib PNGs)
```

## Domain modules

- **forgery_detection.py**: `Pigment`, `Artifact`, `SpectrumReading`;
  `mix_spectrum`, `build_uv_response`, `read_artifact` (noised observation),
  `_nnls_fit` (ridge NNLS), `estimate_mixture`, `screen_reading`,
  `screen_artifact`, `screen_collection`; `ForgeryLevel` enum and
  `ForgeryVerdict`. Detection = anachronism (NNLS + matched filter) + UV +
  residual channels.
- **cover_logistics.py**: `Edge`, `RailNetwork` (validated directed graph),
  `min_cost_flow` (successive shortest paths / Bellman-Ford augmenting paths),
  `golden_ticket_route` (Dijkstra), `plan_transfer`, `pack_circus_trains`;
  `FlowResult`, `TransferPlan`, `LogisticsInfeasibleError`.
- **concealment_sweep.py**: `RadiationSource`, `SweepGrid`,
  `simulate_sweep` (seeded Poisson), `estimate_background` (median filter),
  `anomaly_map` (Poisson z-score), `detect_hotspots` (local maxima),
  `Container`, `mass_anomaly`, `fuse_concealment_report`; `Hotspot`,
  `MassAnomaly`, `ConcealmentReport`.

## Adapter

`mission.py` implements the frozen BOND-API `MissionProvider`
(brief/recon/plan/execute/debrief), runs the three pipelines deterministically,
and returns a JSON-serializable `results` dict plus provenance
(version, seed, sha256 `input_hash`). It also registers three gadgets
(`forge_screen`, `route_cargo`, `sweep_concealment`).

## Figures & manuscript

`figures/` renders `forgery_fingerprints.png`, `rail_network.png`,
`sweep_heatmap.png`. `manuscript_variables.py` hydrates `{{TOKEN}}`s from
`manuscript/config.yaml` plus a live deterministic mission run.

## Boundaries

- Domain modules must not import `infrastructure` or `bond_api`.
- `mission.py` is the only bond_api importer.
- Scripts are thin; business logic stays in `src/`.
