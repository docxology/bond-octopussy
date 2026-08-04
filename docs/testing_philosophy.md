# Testing philosophy — Octopussy: FABERGÉ

The suite follows the BOND guardrails and the template's testing standards:
**real data + computation only, zero mocks**, deterministic fixed-seed
pipelines, and ≥90% line+branch coverage on `src/`.

## Principles

1. **No mock framework.** Tests exercise the real algorithms on real data
   generated from physically-motivated models. Where an abstraction is needed
   (e.g. a deterministic scenario), it is a real data construction — never a
   `MagicMock`/`patch`.
2. **Determinism is asserted.** Pipelines draw only from
   `numpy.random.default_rng(seed)`; tests re-run the same seed and assert
   byte-equality of outputs (e.g. `simulate_sweep`), and assert stable,
   reproducible verdicts across seeds.
3. **Behavioral separation is tested.** Genuine artifacts are never classified
   forged, an all-modern composition is flagged, and the exemplar classes
   separate with a margin (`genuine < borderline < forged`).
4. **Error branches are covered.** Validation errors (bad pigments, empty
   mixtures, non-positive segment cost/capacity, unknown station, unknown
   container category) are asserted with `pytest.raises`.
5. **The protocol is exercised as discovered.** `load_provider('octopussy')`
   validates the film binds and satisfies the frozen `MissionProvider`
   protocol; the full lifecycle runs through `run_mission`.
6. **Live manuscript gate.** Every `{{TOKEN}}` in a numbered manuscript section
   must be emitted by `manuscript_variables.generate_variables()` — the
   cross-reference test scans `manuscript/[0-9][0-9]_*.md` only.
7. **CLI smoke tests** run the thin scripts as subprocesses
   (`sys.executable`, `cwd=project_root`) and assert exit codes and real
   artifacts (e.g. `output/data/mission_outcome.json`, resolved manuscript).

## Coverage target

`uv run pytest tests/ --cov=src --cov-fail-under=90` with branch coverage.
The live measured count/percentage lives in
[`docs/_generated/COUNTS.md`](../docs/_generated/COUNTS.md).

## Test layout

- `test_forgery_detection.py` — pigments, mixing, NNLS unmixing, screening.
- `test_cover_logistics.py` — network validation, min-cost flow, transfer
  planning, packing, unreachable/infeasible paths.
- `test_concealment_sweep.py` — sweep simulation, background/anomaly, hotspot
  detection, mass anomaly, fusion.
- `test_mission.py` — protocol conformance, discovery, gadgets, determinism.
- `test_manuscript_variables.py` — token hydration + live cross-reference gate.
- `test_figures.py` — deterministic PNG generation.
- `test_scripts_smoke.py` — subprocess CLI smoke tests.
