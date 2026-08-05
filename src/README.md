# src/octopussy

Pure, deterministic domain core plus the thin BOND-API adapter for the FABERGÉ
mission.

| Module | Responsibility |
|---|---|
| `forgery_detection.py` | Spectral/UV forgery fingerprinting (ridge NNLS unmixing + UV + matched-filter anachronism). |
| `varnish_ageing.py` | Varnish yellowing kinetics + age dating (Beer–Lambert, golden-section inversion). |
| `cover_logistics.py` | Circus-cover min-cost-flow logistics over a rail corridor + train packing. |
| `rolling_stock.py` | Trainset circulation (Hopcroft–Karp matching / min path cover) + Kuhn–Munkres depot assignment. |
| `concealment_sweep.py` | Radiation + shape/mass anomaly concealed-device sweep. |
| `source_locator.py` | Weighted Gauss–Newton radiation source localization. |
| `mission.py` | Frozen `bond_api` `MissionProvider` (film `octopussy`, codename `FABERGÉ`) + gadget registration. |
| `manuscript_variables.py` | `{{TOKEN}}` hydration from `manuscript/config.yaml` + live mission run. |
| `figures/` | Deterministic matplotlib PNG generation. |

Domain modules import only stdlib + numpy and are importable standalone (no
`infrastructure`, no `bond_api`). `mission.py` is the single `bond_api`
importer.
