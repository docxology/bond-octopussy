# Testing philosophy — Octopussy: FABERGÉ

The package follows the BOND guardrails and the template's testing standards:
**real data + real computation, zero mocks**, deterministic fixed-seed
pipelines, and ≥90% line+branch coverage on `src/`.

The organizing idea is that a passing test must be *capable of failing*. A
green suite that could not have gone red proves nothing, so several rules
below exist specifically to keep assertions falsifiable.

## Principles

1. **No mock framework.** No `MagicMock`, no `mocker.patch`, no
   `unittest.mock`. Tests exercise the real algorithms on data generated from
   the same physically-motivated forward models the mission uses.

   This is affordable because the domain API is *parameterized by data*, not
   by injected dependencies: `screen_reading` takes a pigment `library`,
   `mass_anomaly` takes a `catalog`, `borderline_anachronism` takes an
   `exhibit`, `RailNetwork` takes its `segments`. Testing an alternative world
   means constructing that world, not replacing a collaborator. When a new
   module needs a variant scenario in a test, add the parameter rather than
   reaching for a patch.

2. **Determinism is asserted, not assumed.** Pipelines draw only from
   `numpy.random.default_rng(seed)`. Tests re-run the same seed and assert
   equality of outputs (`simulate_sweep`, `run_faberge`), and assert that
   verdicts remain stable across different seeds. The three inverse solvers
   take no random draws at all: the golden-section fit, Hopcroft–Karp, and
   Gauss–Newton all start from data-derived points and iterate in fixed index
   order.

3. **Behavioral separation is tested, with margin.** Genuine artifacts are
   never classified forged; an all-modern composition is flagged; the exemplar
   classes separate in the order `genuine < borderline < forged`. The
   borderline case is the one that matters — a screen that only catches the
   all-modern fake has not demonstrated anything a threshold could not.

4. **Every `raise` is covered.** Validation errors are asserted with
   `pytest.raises` and, where the message carries meaning, with `match=`:
   empty pigment names, empty mixtures, non-positive segment cost or capacity,
   an unknown station, a self-transfer, an unknown container category, a
   non-square cost matrix, a transmittance outside `[0, 1]`, a claimed
   provenance that does not predate the current year.

5. **Termination is a property worth testing.** `min_cost_flow` once looped
   forever on a `source == sink` request (an empty augmenting path pushed zero
   units per iteration). It now raises, and
   `test_min_cost_flow_rejects_self_transfer` pins that. Any solver with a
   `while` loop deserves at least one test of the input that could stall it.

6. **The protocol is exercised as *discovered*, not as imported.**
   `load_provider('octopussy')` resolves the film the way the orchestrator
   does, and the result is checked with `isinstance(..., MissionProvider)`
   against the runtime-checkable protocol. The full lifecycle also runs
   through `bond_api.run_mission`.

7. **The manuscript is gated in both directions.** Three tests together make
   hand-authored metrics impossible:
   - every token used in a numbered section must be emitted by
     `generate_variables()`;
   - every token emitted must be referenced by some section (an unused token
     is dead weight and, worse, unreviewed);
   - abstract, results, and conclusion prose must contain **no bare numeral**
     outside a code span or a resolved token.

   A fourth test binds the bibliography: every `@key` cited must exist in
   `references.bib`, and every entry in `references.bib` must be cited. Both
   directions matter — a one-way check lets an uncited (therefore unreviewed)
   reference sit in the file indefinitely, which is exactly how a fabricated
   source survives.

8. **Derived values must be proven derived.** `FABERGE_NUM_DETECTORS` was once
   produced by a helper that returned a literal `100`, which would have gone
   stale the moment the lattice changed. A test now asserts the token equals
   `SWEEP_GRID.nx * SWEEP_GRID.ny`. Any constant that *looks* derived should
   have a test proving it tracks its source.

9. **CLI smoke tests run the real scripts.** Each thin script is executed as a
   subprocess (`sys.executable`, `cwd=project_root`) and checked for exit code
   and real artifacts on disk (`output/data/mission_outcome.json`, the
   figures, the resolved manuscript). The token-generation test copies the
   tree to `tmp_path` first so it never mutates tracked state.

## Anti-vacuity rules for new tests

- Never assert something that holds for any implementation. `len(filtered) <=
  len(unfiltered)` is true of every monotone filter and passes even if the
  filter is ignored — assert a *strict* reduction and check the surviving
  elements satisfy the criterion.
- Never assert a field that cannot vary. `FlowResult.feasible` was `True` in
  every constructed instance, so `assert result.feasible` could not fail; the
  field was removed and the tests now assert routed flow and capacity limits.
- When fixing a defect, write the test that reproduces it *first*, and check
  it fails against the unfixed code.
- When adding a scanning or cross-referencing test, assert the scan set is
  non-empty. A sweep that examined zero files is vacuous, not clean.

## Coverage

`uv run pytest tests/ --cov=src --cov-fail-under=90` with branch coverage
enabled (`branch = true` in `pyproject.toml`). The gate is the contract; the
currently measured figure lives in
[`_generated/COUNTS.md`](_generated/COUNTS.md) and is regenerated, never
quoted into prose elsewhere.

## Test layout

| File | Covers |
|---|---|
| `test_forgery_detection.py` | Pigment/artifact validation, mixing, UV response, ridge NNLS unmixing, screening, class separation. |
| `test_varnish_ageing.py` | Yellowing law, Beer–Lambert transmittance, golden-section age inversion, era verdicts, spectrum ageing, validation errors. |
| `test_cover_logistics.py` | Network validation, min-cost flow (including capacity limits, infeasibility, and self-transfer rejection), transfer planning, Dijkstra routing, train packing. |
| `test_rolling_stock.py` | Trip validation, successor compatibility, Hopcroft–Karp matching, minimum trainsets, itinerary chains, Kuhn–Munkres assignment. |
| `test_concealment_sweep.py` | Sweep simulation and determinism, background/anomaly maps, hotspot detection and thresholding, mass anomaly, fused report ranking. |
| `test_source_locator.py` | Forward model, weighted residual, Gauss–Newton recovery and diagnostics, uncertainty, the `DetectorLattice` protocol, degenerate inputs. |
| `test_mission.py` | Protocol conformance and discovery, the `PIPELINES` invariant, derived sweep constants, provenance hashing, gadget registration, debrief coverage, layer-purity source scan. |
| `test_manuscript_variables.py` | Config loading, token hydration, strict tree resolution, the four manuscript/bibliography gates, derived-token proofs. |
| `test_figures.py` | Deterministic PNG generation for all three figures. |
| `test_scripts_smoke.py` | Subprocess execution of every thin CLI and the artifacts each writes. |
