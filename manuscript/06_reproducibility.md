# Reproducibility

Reproducibility is the central guarantee of this package
({{FABERGE_IDENTITY}} v{{FABERGE_VERSION}}).

- **Fixed seed.** Every pipeline draws only from
  `numpy.random.default_rng({{FABERGE_SEED}})`; there is no global or untracked
  randomness, and no wall-clock value is written into any persisted artifact.
  The three inverse solvers — the golden-section varnish fit, the Hopcroft–Karp
  matching, and the Gauss–Newton localization — take no random draws at all:
  each starts from a data-derived point and iterates in fixed index order.
- **Live provenance.** Each mission outcome carries `package_version`, the
  fixed `seed`, and an `input_hash` — a sha256 fingerprint of the mission's
  defining inputs (codename, objectives, and plan) — so an outcome can be
  audited without re-running the film.
- **Generated artifacts.** Figures and manuscript variables are regenerated
  from source by `scripts/mission_execute.py` and
  `scripts/z_generate_manuscript_variables.py`; none are hand-maintained
  snapshots. Regenerating leaves a byte-identical, git-clean tree.
- **No hand-authored metrics.** Every number in the abstract, results, and
  conclusion arrives as an injected manuscript token resolved from
  `src/octopussy/manuscript_variables.py` against a live run. A test asserts
  both directions of that contract: no section may use a token the generator
  does not emit, and no generated token may go unreferenced.
- **No mocks.** Tests use real computation only; deterministic reference
  providers implement the real BOND-API protocol.

Report artifacts live under `output/` (regenerated): the mission outcome, the
rendered figures, and the resolved manuscript tree.
