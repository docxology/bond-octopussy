# Experimental setup

All experiments are configured through `manuscript/config.yaml` and the module
constants in `src/octopussy/`. The pipeline is deterministic: every random
draw comes from `numpy.random.default_rng(seed)` with seed {{FABERGE_SEED}}.

- Pigment library: {{FABERGE_NUM_PIGMENTS}} pigments across 24 UV-VIS bands
  (320–760 nm).
- Exhibit: {{FABERGE_NUM_ARTIFACTS}} artifacts screened end-to-end.
- Corridor: {{FABERGE_NUM_SEGMENTS}} directed rail segments.
- Sweep: {{FABERGE_NUM_DETECTORS}} detectors on a 10×10 lattice; scenario of
  {{FABERGE_NUM_CONTAINERS}} cargo containers screened for mass anomaly.

Environment used for this report: Python {{PYTHON_VERSION}}. Artifacts were
generated on {{GENERATION_TIMESTAMP}} (UTC). Versions of the scientific stack
(numpy, matplotlib) are pinned through the package's `pyproject.toml`; the
frozen protocol dependency `bond-api` is resolved as a local path source.
