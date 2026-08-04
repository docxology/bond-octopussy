# Reproducibility

Reproducibility is the central guarantee of this package.

- **Fixed seed.** Every pipeline draws only from `numpy.random.default_rng({{FABERGE_SEED}})`; there is no global or untracked randomness, and no wall-clock value is written into any persisted artifact.
- **Live provenance.** Each mission outcome carries `package_version`, the
  fixed `seed`, and an `input_hash` — a sha256 fingerprint of the mission's
  defining inputs (codename, objectives, and plan) — so an outcome can be
  audited without re-running the film.
- **Generated artifacts.** Figures and manuscript variables are regenerated
  from source by `scripts/mission_execute.py` and
  `scripts/z_generate_manuscript_variables.py`; none are hand-maintained
  snapshots. Regenerating leaves a byte-identical, git-clean tree.
- **No mocks.** Tests use real computation only; deterministic reference
  providers implement the real BOND-API protocol.

Report artifacts live under `output/` (regenerated): the mission outcome,
rendered figures, and the resolved manuscript tree.
