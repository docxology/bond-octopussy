# src/octopussy

Pure, deterministic domain core plus the thin BOND-API adapter for the FABERGÉ
mission.

| Module | Responsibility |
|---|---|
| `forgery_detection.py` | Spectral/UV forgery fingerprinting (ridge NNLS unmixing + UV + matched-filter anachronism). |
| `cover_logistics.py` | Circus-cover min-cost-flow logistics over a rail corridor + train packing. |
| `concealment_sweep.py` | Radiation + shape/mass anomaly concealed-device sweep. |
| `mission.py` | Frozen `bond_api` `MissionProvider` (film `octopussy`, codename `FABERGÉ`) + gadget registration. |
| `manuscript_variables.py` | `{{TOKEN}}` hydration from `manuscript/config.yaml` + live mission run. |
| `figures/` | Deterministic matplotlib PNG generation. |

Domain modules import only stdlib + numpy and are importable standalone (no
`infrastructure`, no `bond_api`). `mission.py` is the single `bond_api`
importer.
