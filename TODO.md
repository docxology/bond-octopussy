# TODO — octopussy (FABERGÉ)

`octopussy` is the BOND-suite film package for *Octopussy* (1983), mission
codename **FABERGÉ**. It implements the film's three investigative problems —
authenticity, cover logistics, concealment — as six pure deterministic domain
modules under `src/octopussy/`, paired one headline detector + one depth module
per problem, exposed behind the frozen `bond_api` `MissionProvider` contract in
`src/octopussy/mission.py`. Verified state: see the
[Round-2 record](#round-2-2026-08-06) below and
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md), which carries the last
measured counts. Ruff check, ruff format --check, and mypy on `src/ scripts/`
are clean, and the exemplar-leftover gate returns only permitted lineage notes.

This file is **open work only**; closed items are marked in place with a pointer
to the [Round-2 record](#round-2-2026-08-06) below, which carries the last
measured state. Phases before Round-2 are not restated — git history is the
record.

---

## Open work

> Items marked **closed in Round-2** are kept here only as a pointer: the fix,
> its regression test, and the final gate numbers are in the
> [Round-2 record](#round-2-2026-08-06) below. C1, C2, C3 and V4 closed there;
> V1–V3 remain open by deliberate deferral.

### Correctness

#### C1 — The screen names pigments the artifact does not contain — **closed in Round-2**

`screen_artifact` reports a fitted anachronism tuple derived from the unmixing
solution, filtered only by an abundance floor of `1e-3`
(`src/octopussy/forgery_detection.py:355-357`). On the shipped exhibit that
admits a component the artifact does not have: `gilt_fake`'s authored mixture
is `chalk 0.5 / cadmium_yellow 0.30 / acrylic_varnish 0.20`
(`src/octopussy/forgery_detection.py:440`), yet the persisted mission outcome
lists

```
"anachronistic pigment(s) detected: acrylic_varnish, cadmium_yellow, phthalocyanine_blue"
```

`phthalocyanine_blue` (introduced 1935) is unmixing residue, not a detection.
The verdict level is unaffected, but the *reason string* — the part a reader
treats as the finding — is wrong, and it is written into
`output/data/mission_outcome.json` and consumed by the debrief.

- **Done looks like:** on `forge.DEFAULT_EXHIBIT`, every name in
  `ForgeryVerdict.anachronistic` is a pigment present in that artifact's
  authored mixture — either by raising the abundance floor above the residue
  level, or by intersecting the fitted tuple with the authored mixture before
  composing reasons. Whichever route, a new test in
  `tests/test_forgery_detection.py` asserts the containment for every artifact
  in the exhibit and fails on today's code.
- **Command** (run from the package root; verified to reproduce the defect
  today — prints `gilt_fake ['phthalocyanine_blue']`, and every list must be
  empty when this is closed):

  ```bash
  uv run python scripts/mission_execute.py
  uv run python - <<'PY'
  import json, sys
  sys.path.insert(0, "src")
  import octopussy.forgery_detection as f
  d = json.load(open("output/data/mission_outcome.json"))
  authored = {a.name: {p for p, _ in a.mixture} for a in f.DEFAULT_EXHIBIT}
  for v in d["results"]["forgery"]["verdicts"]:
      named = [p for r in v["reasons"] if "anachronistic" in r
               for p in r.split(": ")[1].split(", ")]
      print(v["artifact"], [p for p in named if p not in authored[v["artifact"]]])
  PY
  ```

#### C2 — `cover_logistics` module functions bypass the accessors that exist — **closed in Round-2**

`RailNetwork` already exposes read-only `nodes` and `segments` properties
(`src/octopussy/cover_logistics.py:120-126`), but ten module-level call sites
reach into `network._segments` / `network._nodes` directly:
lines **133, 151, 254, 275, 315, 321, 322, 360, 383, 394**. It works only
because they are same-module neighbours; any future subclass or wrapper that
satisfies the public surface silently breaks the solver.

- **Done looks like:** zero `network._segments` / `network._nodes` occurrences
  outside the class body; the min-cost-flow and Dijkstra paths read through
  `.segments` / `.nodes`; the suite still passes with unchanged results in
  `output/data/mission_outcome.json`.
- **Command:**
  `rg -n 'network\._segments|network\._nodes' src/octopussy/cover_logistics.py` → no matches;
  then `uv run pytest tests/ --cov=src --cov-fail-under=90`.

#### C3 — `varnish_ageing.DEFAULT_BANDS` duplicates the forgery band grid — **closed in Round-2**

`src/octopussy/varnish_ageing.py:80` defines
`np.linspace(320.0, 760.0, 24)` independently of
`src/octopussy/forgery_detection.py:65` `WAVELENGTH_BANDS`. The two are equal
by construction, and since the varnish channel now multiplies an exhibit
spectrum by a transmittance band-for-band
(`src/octopussy/mission.py:253-316`), a divergence would produce silently wrong
numbers rather than an error.
`tests/test_mission.py:236` binds them with an array-equality assertion, so the
silent-failure risk is closed — but the duplication itself remains, and the
domain-purity rule forbids `varnish_ageing` importing `forgery_detection`.

- **Done looks like:** one grid definition, with the second module deriving
  from it without violating the pure-module layer contract (e.g. a shared
  private `_bands.py` both import, asserted by
  `tests/test_mission.py::test_mission_uses_no_infrastructure_imports`
  continuing to pass).
- **Command:**
  `rg -n 'linspace\(320\.0, 760\.0' src/octopussy/` → exactly one hit;
  then `uv run pytest tests/ -q`.

---

### Verification

Claims that are true today but not bound by a test that could fail.

#### V1 — No negative control near the anachronism boundary

Every genuine artifact in `forge.DEFAULT_EXHIBIT`
(`src/octopussy/forgery_detection.py:434-441`) uses pigments introduced
centuries before its claimed year — `tsar_egg` (1910) and `ballet_case` (1912)
draw on lead white, lapis, vermilion, chalk, malachite, umber, shellac. No
honest object sits *close* to the boundary, so the false-positive rate of the
matched-filter anachronism channel is untested. The claim the package can
support today is "catches these fakes", not "distinguishes fakes from honest
objects near the boundary".

- **Done looks like:** the exhibit contains a genuine piece whose newest
  pigment post-dates nothing — e.g. an honest 1915 object using
  `cadmium_yellow` (introduced 1910, `forgery_detection.py:170`) — and a test
  asserts it screens `GENUINE` or `LIKELY_GENUINE`. Note this shifts
  `ARTIFACT_COUNT`, the flagged count, and the manuscript tokens that quote
  them (see the coupling note in **Known limitations**).
- **Command:** `uv run pytest tests/test_forgery_detection.py -q -k boundary`

#### V2 — Detection thresholds are calibrated on the exhibit that evaluates them

`_level_for_score` (`src/octopussy/forgery_detection.py:370-384`) hard-codes
0.25 / 0.30 / 0.48, and its own docstring states these were fitted to the
measured separation of the four exemplar artifacts the suite then screens.
Calibration and evaluation share data, so the reported separation is not an
independent result.

- **Done looks like:** the exhibit is widened, thresholds are re-derived on a
  held-out subset, and a test asserts the evaluated artifacts were excluded
  from the fit (e.g. a module-level constant naming the calibration set, with
  the screening test asserting disjointness).
- **Command:** `uv run pytest tests/test_forgery_detection.py -q -k threshold`

#### V3 — The trace-anachronism regime is untested

`FABERGE_BORDERLINE_MODERN_PCT` resolves to **50** — the exhibit's least-modern
fake (`gilt_fake`) is still half modern by weight. Nothing here shows the
matched-filter channel resolving a few percent of modern material out of an
otherwise period-correct object, which is the case that would actually be hard.
The manuscript now quotes the fraction instead of characterizing it
(`manuscript/03_results.md:14-28`, `manuscript/07_scope_and_related_work.md:23-27`),
so the prose is honest — but the regime is still unexercised.
**Carried over unresolved from the FABERGÉ audit remediation.**

- **Done looks like:** an artifact with ≲10 % anachronistic weight is in the
  exhibit, `borderline_anachronism()`
  (`src/octopussy/manuscript_variables.py:58`) selects it, and
  `tests/test_manuscript_variables.py:176` (`test_borderline_case_is_actually_flagged_by_the_screen`)
  passes against it — or the test records that it is *not* flagged, which is
  itself the honest result.
- **Command:** `uv run pytest tests/test_manuscript_variables.py -q -k borderline`

#### V4 — Uncovered defensive branches in three modules — **closed in Round-2**

Measured this session: `cover_logistics.py` **93.31 %** (missing
`172->183, 192, 195, 206, 212, 277-278, 318, 392, 401, 406`),
`source_locator.py` **93.62 %** (missing `213->243, 231-237, 239`),
`rolling_stock.py` **96.54 %** (missing `93->91, 117-119, 124->123`). All are
above the 90 % gate, but they are precisely the paths that run when something
goes wrong: the Bellman–Ford augmenting-path failure returns, the Gauss–Newton
line-search halving loop (`source_locator.py:230-239`), and the Hopcroft–Karp
`dfs` failure branch (`rolling_stock.py:117-119`).

- **Done looks like:** constructed degenerate inputs reach them — a network
  with a zero-capacity bottleneck, a disconnected sink, an ill-conditioned
  detector geometry that forces line-search halving, a trip set with no
  augmenting path — and the three modules report 100 % or the remainder is
  documented as unreachable with the reason.
- **Command:**
  `uv run pytest tests/ --cov=src --cov-report=term-missing` → the three
  Missing columns above are empty.

---

### Documentation

**None open.** Checked this session: `README.md` (module table, frozen-surface
table, gate table) matches `src/octopussy/` and `mission.py`; `AGENTS.md` gate
list runs clean end to end; `docs/_generated/COUNTS.md` carries the last
measured counts, and the Round-2 record below carries the gate results;
`manuscript/06_reproducibility.md` and `docs/agent_instructions.md:33` state
the no-wall-clock rule, and `rg -n 'GENERATION_TIMESTAMP'` finds no live
emitter (only the historical note at
`src/octopussy/manuscript_variables.py:111`). The five `template_code_project`
hits are lineage notes, which the gate permits.

---

### Extension

Genuine future work; nothing here is currently wrong.

#### E1 — Per-resin varnish time constant

τ is fixed for all resins and illumination histories in `varnish_ageing.py`.
Parameterize τ per resin and fit it jointly with age.
**Done:** `estimate_age` accepts a resin identity, the exhibit's shellac and
acrylic surfaces use different τ, and a test shows a wrong-τ fit produces a
measurably worse residual than the right one.

#### E2 — A second, non-saturating age observable

With τ = 40 y a century-old surface sits past three time constants, so recovered
age scatters wider than the consistency tolerance (measured by
`age_recovery_scatter`). Removing the ceiling needs a second observable that
does not saturate — a cross-linking or solubility proxy — not a better fit to
the same one.
**Done:** the varnish block in `mission.py` reports a second observable whose
scatter on the century-old surface is inside the tolerance, and the manuscript
can state a *confirmation* rather than a failure to reject.

#### E3 — Sweep physics: attenuation, scattering, energy resolution

`concealment_sweep.py` draws Poisson counts about an inverse-square field with
no attenuation through intervening cargo and no energy channel — the
discriminant a real portal monitor leans on hardest.
**Done:** a two-detector coincidence model or a coarse energy channel exists,
with a test showing it separates a shielded source from an unshielded one where
the current single-channel model cannot.

#### E4 — Delegate provenance persistence to `bond-utilities`

`mission.py:163-171,456-459` computes its own sha256 `input_hash`.
`bond_utilities.mission_io.record_provenance_outcome`
(`../bond-utilities/src/bond_utilities/mission_io.py:153`) now exists and could
own this. **Caveat that must be handled first:** that helper writes
`started_at` from `datetime.now(timezone.utc)` unless the `now` argument is
injected, which would break octopussy's byte-identity reproducibility claim in
`manuscript/06_reproducibility.md`. `octopussy` also does not currently depend
on `bond-utilities` (`pyproject.toml:17-22` lists `bond-api` only).
**Done:** mission outcomes persist through that helper with `now` pinned, the
results dict shape is unchanged, and
`tests/test_manuscript_variables.py::test_regeneration_is_byte_identical` still
passes. Not blocking — provenance is already emitted correctly.

---

## Known limitations (not bugs)

Accepted and deliberately out of scope. Do not re-litigate these; if you
disagree, change the manuscript claim first.

- **Ground truth is authored, so every result is estimator behaviour.** The
  pigment mixtures, the true varnish ages, the emitter position, and the rail
  schedule are all defined inside this package. No independent ground truth is
  constructible inside a simulation. This was raised in the audit and resolved
  by narrowing the claim rather than by changing code:
  `manuscript/07_scope_and_related_work.md` now names the ground truth as
  authored and reports the measured error bar beside every verdict. The honest
  scope is "these estimators behave this way against a known truth", never
  "this is a measurement of a physical object".
- **The pairing gives independence of *observable*, not of sample.** All six
  pipelines run on the same synthetic scenario. A depth module agreeing with
  its headline detector is evidence only in proportion to that module's own
  measured uncertainty — which is why every depth claim ships with its scatter.
- **Varnish dating cannot confirm old provenance.** Past ~3τ the kinetics
  saturate; the channel is a *rejection* instrument only. A "consistent"
  verdict on a century-old surface is a failure to reject and carries no
  information in either direction. Stated in
  `manuscript/07_scope_and_related_work.md` and measured by
  `age_recovery_scatter`. Removing this needs E2, not a better fit.
- **Widening the exhibit is a coupled change.** V1, V2 and V3 all require a
  fifth artifact, and adding one shifts `ARTIFACT_COUNT`, the flagged count,
  the worst scorer, the `_level_for_score` thresholds, and the manuscript
  tokens that quote all of them. This coupling is why the audit remediation
  stated V3 as a limitation instead of fixing it — it is a deliberate deferral,
  not an oversight. Land the exhibit change as its own commit.
- **Models are physically motivated but illustrative.** The 14-pigment library,
  the rail corridor, and the container catalog are deterministic fixtures, not
  instrumentation. No claim of fidelity to real spectrometers, rail networks,
  or scintillation detectors is made anywhere.

---

## Standing constraints (not tasks — do not "complete" these)

- The `MissionProvider` surface (`brief`/`recon`/`plan`/`execute`/`debrief`),
  `gadget_registry`, and `register_gadgets` are **frozen**: bond-cli, the
  coordinator, and the orchestrator consume them across packages.
- Figures and manuscript variables are regenerated, never hand-maintained.
- No mock framework, ever. Deterministic seeds, always.
- Repository: upstream `https://github.com/docxology/bond-octopussy`, default
  branch `main`. Commits are path-scoped to this directory.

---

## Verification

Run in this order from the repository root (`bond-octopussy`). `uv sync --extra dev`
first — `bond-api` resolves from the recorded copy at `vendor/bond-api`, which
`scripts/vendor.py --check` verifies. Under a restrictive sandbox `uv`
cannot write its cache; `Failed to initialize cache` is an environment
restriction, not a package failure.

| # | Gate | Command | Green means |
|---|---|---|---|
| 1 | Tests + branch coverage | `uv run pytest tests/ --cov=src --cov-fail-under=90` | 0 failed, 0 skipped, coverage ≥ the 90 % floor — live figures in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md), never quoted here |
| 2 | Lint | `uv run ruff check src/ scripts/ tests/` | `All checks passed!` — **not reached as of 2026-11-04**: see D2 below |
| 3 | Format | `uv run ruff format --check src/ scripts/ tests/` | every file already formatted — green only because the table below states `line-length = 120`; at ruff's default 88 it reported 23 files (D1) |
| 4 | Types | `uv run mypy src/ scripts/` | no issues found |
| 5 | Manuscript resolves, no unresolved token | `uv run python scripts/z_generate_manuscript_variables.py` | exit 0, writes `output/manuscript/` |
| 6 | No exemplar leftovers | `rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**'` | the three lineage notes and nothing else: `README.md`, `STANDALONE.md`, this file. Adding those three as `--glob '!…'` prints `Clean`, and *that* spelling can fail — the two rule copies are written bracket-split so the audit cannot hit its own prose (D4) |
| 7 | Recorded copies match their provenance | `uv run python scripts/vendor.py --check` | `vendor/bond-api: ok`, 0 finding(s) |
| 8 | Clean tree after a path-scoped commit | `git status --short` | empty |

Per-module coverage lives in [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md)
(regenerated, never restated here; **V4** was closed in Round-2, which took the
two reachable modules that were still below 100 % up to 100 %).

---

## Round-2 (2026-08-06)

Round-2 deep-improvement pass: hostile review, defect fixes with regression
tests, manuscript depth, gate closure. **Baseline:** 155 tests passed, 97.43 %
line+branch coverage on `src/`, ruff/mypy clean. **Final:** 168 tests passed,
0 failed, 0 skipped, 99.36 % coverage, ruff check/format/mypy clean, manuscript
resolves with no unresolved token.

### Defects found and fixed (each with a regression test)

- **C1 — the screen named pigments the artifact does not contain.** The
  `anachronistic` tuple was cut straight from the full-fit abundance
  (`w > 1e-3`), so collinear "white" pigments picked up spurious weight: a
  *genuine* tsar_egg and ballet_case reported acrylic_varnish,
  phthalocyanine_blue and titanium_white; gilt_fake reported
  phthalocyanine_blue. Worse than the backlog entry claimed — the hallucination
  hit honest objects, not just the residue case. **Fix:** a per-pigment
  residual-improvement descriptor (`_detect_anachronistic`,
  `_ANACH_DETECT_LEVEL = 0.25`) — a modern pigment is *named* only when
  admitting it to the era-consistent fit explains ≥ a quarter of the
  era-inconsistent residual variance. Validated over 100 noise seeds: zero
  false positives; forged_dupe's phthalocyanine_blue and gilt_fake's
  cadmium_yellow still detected; verdicts and scores byte-unchanged. The
  abundance floor could not be tuned to fix this (flat absent pigments carry
  ~0.27 spurious abundance, larger than some real ones), which is why a
  residual test rather than a threshold was the fix. Evidence:
  `tests/test_forgery_detection.py::test_no_hallucinated_anachronistic_pigments`
  (fails on the old code — it lists modern pigments on genuine artifacts), and
  `output/data/mission_outcome.json` reasons now name only pigments present in
  the artifact. Also fixed the latent `_compose_reasons` placeholder that
  printed "anachronistic pigment(s) detected: yes" when a signal existed but no
  pigment cleared the level (`test_compose_reasons_omits_placeholder_when_no_single_pigment_detects`).
- **C2 — `cover_logistics` module functions bypassed the public accessors.**
  Ten call sites read `network._segments` / `network._nodes` / `network._out`
  directly, so any wrapper satisfying the public `.segments` / `.nodes`
  surface silently broke the solver. **Fix:** all solver/planner/Dijkstra paths
  now read through the properties; the now-dead `_out` adjacency was removed.
  Evidence: `rg -n 'network\._segments|network\._nodes|network\._out'` → no
  matches outside the class body; `tests/test_cover_logistics.py::test_solver_goes_through_public_accessors`
  runs min-cost flow, the planner, and Dijkstra on a proxy that exposes only
  the public surface.
- **C3 — `varnish_ageing.DEFAULT_BANDS` duplicated the forgery grid.**
  Two `np.linspace(320, 760, 24)` definitions made a silent band drift
  possible. **Fix:** new `src/octopussy/_bands.py` is the single definition;
  `forgery_detection.WAVELENGTH_BANDS` and `varnish_ageing.DEFAULT_BANDS` are
  the *same array object* by import. Evidence: `rg 'linspace(320.0, 760.0'` →
  one hit (in `_bands.py`); `tests/test_mission.py::test_bands_are_a_single_shared_definition`
  asserts identity, not mere equality.

### Defensive branches exercised (V4)

Degenerate-input tests now reach the "when something goes wrong" paths:
Gauss–Newton iteration-budget exhaustion, line-search halving, and the
two-detector degeneracy (`test_source_locator.py`); the recursive matching
reassignment and layered BFS (`test_rolling_stock.py::test_maximum_matching_reassigns_via_recursive_augment`);
the min-cost-flow reverse-arc cancellation path with node-flow conservation
(`test_cover_logistics.py::test_min_cost_flow_with_arc_cancellation_is_conserving`),
a disconnected in-graph sink, and Dijkstra stale-heap entries; and the forgery
noiseless / all-zero measurement guards. Result: `forgery_detection.py` and
`rolling_stock.py` are now **100.00 %**; `source_locator.py` 98.58 %;
`cover_logistics.py` 96.96 %.

**Documented as unreachable by construction** (defensive guards, not fixable by
more tests): `cover_logistics.py` `170->181` (Bellman–Ford outer loop cannot
exhaust without a negative-cost cycle, absent by construction), `190` and `403`
(parent chains are always complete when the target is reachable), `210`
(relax() only admits moves with positive availability, so the bottleneck is
always > 0), `316` (a valid min-cost flow always admits a full source→sink
decomposition); `source_locator.py` `239` (the no-improvement-after-halving
stop — a safety net that the well-conditioned inverse-square forward model
never triggers across the probe geometries tried).

### Manuscript depth

- New engine-bound figure `figures/varnish.py` → `varnish_scatter.png`:
  recovered varnish age vs true coating age across the saturation, rendered
  from live `age_recovery_scatter` runs; byte-identical across regenerations.
- `03_results.md`: new "Results at a glance" table (one line per pipeline) and
  a per-artifact forgery-verdict table (disposition / score / attributed
  anachronistic pigments) — every cell a manuscript token hydrated from the
  live run; new `FABERGE_VERDICT_N_*` tokens in `manuscript_variables.py`
  (positional over the exhibit, so renames cannot stale the table).
- `02_methodology.md`: documents the attributable-evidence rule for naming
  anachronistic pigments. All token cross-reference tests pass in both
  directions.

### Gates (final, this session)

| # | Gate | Result |
|---|---|---|
| 1 | `uv run pytest tests/ --cov=src --cov-fail-under=90` | **168 passed**, 0 failed/skipped, **Total coverage 99.36 %** |
| 2 | `uv run ruff check src/ scripts/ tests/` | All checks passed |
| 3 | `uv run ruff format --check src/ scripts/ tests/` | 41 files already formatted |
| 4 | `uv run mypy src/ scripts/` | Success: no issues found in 23 source files |
| 5 | `scripts/z_generate_manuscript_variables.py` | exit 0; 9 sections resolved, 4 figures rendered |
| 6 | exemplar-leftover scan | 5 hits, all lineage notes |
| 7 | clean tree after commit | empty |

### Left for a future round

- **V1/V2/V3 remain deliberately deferred** (per the "Known limitations"
  coupling note): any of them requires widening the exhibit, which shifts
  `ARTIFACT_COUNT`, the flagged count, the worst scorer, the
  `_level_for_score` thresholds, and the manuscript tokens quoting them. Land
  that as its own commit when a fifth artifact is wanted.
- **E1–E4 (extensions)** unchanged: per-resin τ, a second non-saturating age
  observable, sweep attenuation/energy channels, and delegating provenance to
  `bond-utilities` (the `datetime.now` caveat in E4 still applies).
