# Experimental setup

All experiments are configured through `manuscript/config.yaml` and the module
constants in `src/octopussy/`. The pipeline is deterministic: every random
draw comes from `numpy.random.default_rng(seed)` with seed {{FABERGE_SEED}}.

## Scenario constants

| Pipeline | Configuration |
|---|---|
| Forgery detection | {{FABERGE_NUM_PIGMENTS}}-pigment library over {{FABERGE_NUM_BANDS}} UV-VIS bands ({{FABERGE_BAND_MIN_NM}}–{{FABERGE_BAND_MAX_NM}} nm) |
| Forgery detection | Exhibit of {{FABERGE_NUM_ARTIFACTS}} artifacts screened end-to-end |
| Varnish ageing | Exhibit surfaces *{{FABERGE_VARNISH_GENUINE_ARTIFACT}}* (claimed {{FABERGE_VARNISH_CLAIMED}}) and *{{FABERGE_VARNISH_FAKE_ARTIFACT}}*, dated on the same band grid |
| Varnish ageing | Authored true ages {{FABERGE_VARNISH_TRUE_AGE}} y and {{FABERGE_VARNISH_FAKE_TRUE_AGE}} y; ±{{FABERGE_VARNISH_TOLERANCE}} y consistency tolerance; {{FABERGE_VARNISH_TRIALS}} noise realizations per scatter |
| Cover logistics | {{FABERGE_NUM_SEGMENTS}} directed rail segments across {{FABERGE_NUM_STATIONS}} stations |
| Cover logistics | {{FABERGE_LOGISTICS_UNITS}} payload units, {{FABERGE_LOGISTICS_DEADLINE}}-minute deadline |
| Rolling stock | {{FABERGE_ROLLING_TRIPS}} scheduled circus trips |
| Concealment sweep | {{FABERGE_NUM_DETECTORS}} detectors on a {{FABERGE_GRID_NX}}×{{FABERGE_GRID_NY}} lattice |
| Concealment sweep | {{FABERGE_NUM_CONTAINERS}} cargo containers against {{FABERGE_NUM_CATEGORIES}} density profiles |

Every value in this table is injected from the live package surface rather
than transcribed, so changing a scenario constant in `src/` changes this table
on the next render.

## Environment

Environment used for this report: Python {{PYTHON_VERSION}}. No generation
timestamp is recorded: a wall-clock stamp used to be injected here and written
into `output/data/manuscript_variables.json`, which made two regenerations
differ and falsified the byte-identity claim in the reproducibility section.
Determinism was judged the more useful property, and mission provenance already
carries an `input_hash`. Versions of the scientific stack (numpy, matplotlib)
are pinned through the package's `pyproject.toml`; the frozen protocol
dependency `bond-api` is resolved as a local path source.

The full run is driven by `scripts/mission_execute.py` (mission outcome and
figures) and `scripts/z_generate_manuscript_variables.py` (token hydration and
the resolved manuscript tree). Neither requires network access.
