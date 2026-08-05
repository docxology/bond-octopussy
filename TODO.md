# octopussy TODO

Forward-only backlog for the FABERGÉ film package. **Remaining work only** —
completed phases are not recorded here; the git history is the record, and
`README.md` plus `docs/architecture.md` describe what exists today.

## Open — scientific validity

These are limitations that weaken specific claims. They are stated in
`manuscript/07_scope_and_related_work.md`; the work is to remove them, not to
document them again.

- [ ] **No negative control near the anachronism boundary.** The exhibit has
      no *genuine* period piece whose pigments sit close to its claimed year,
      so the false-positive rate of the anachronism channel is untested. Add
      such an artifact (e.g. an honest 1915 piece using cadmium yellow,
      introduced 1910) and assert it screens genuine. Until then the forgery
      claim is "catches these fakes", not "distinguishes fakes from honest
      objects near the boundary".
- [ ] **Detection thresholds are calibrated on the exhibit that tests them.**
      `_level_for_score` thresholds were fitted to the measured separation of
      the same four artifacts the suite screens. Widen the exhibit, then
      re-derive the thresholds from a held-out set so calibration and
      evaluation stop sharing data.
- [ ] **Varnish kinetics use a single time constant.** τ is fixed for all
      resins and illumination histories. Either parameterize τ per resin and
      fit it jointly with age, or narrow the manuscript claim from "dates the
      surface" to "tests consistency against a claimed provenance".
- [ ] **The sweep model omits attenuation and spectroscopy.** Counts are
      Poisson about an inverse-square field with no scattering, no attenuation
      through intervening cargo, and no energy resolution — the discriminant a
      real portal monitor leans on hardest. A two-detector coincidence model
      or a coarse energy channel would be the next real increment.

## Open — engineering

- [ ] **`cover_logistics` reaches into `RailNetwork._segments` and `._nodes`
      from module-level functions.** It works because they are same-module
      neighbours, but the private access is load-bearing across ~6 call sites.
      Promote a read-only accessor and use it.
- [ ] **`varnish_ageing.DEFAULT_BANDS` duplicates the forgery band grid.** The
      two are equal by construction and by comment, not by code. If they ever
      diverge, `mission.run_faberge` silently compares spectra on mismatched
      grids. Derive one from the other or assert their equality in a test.
- [ ] **Uncovered branches.** `cover_logistics` (93.3%) and `source_locator`
      (93.6%) carry the package's remaining uncovered lines — mostly
      defensive paths in the augmenting-path search and the Gauss–Newton line
      search. Well above the 90% gate, but these are exactly the paths that
      run when something goes wrong. Reach them with constructed degenerate
      networks and ill-conditioned detector geometries.

## Open — suite integration

- [ ] **bond-utilities provenance.** The adapter computes its own
      `input_hash`. When `bond-utilities` ships, consider delegating
      provenance persistence to
      `bond_utilities.mission_io.record_provenance_outcome`. Acceptance:
      mission outcomes persist through that helper without changing the
      results dict. Not blocking — provenance is already emitted.

## Standing constraints (not tasks — do not "complete" these)

- The `MissionProvider` surface (`brief`/`recon`/`plan`/`execute`/`debrief`),
  `gadget_registry`, and `register_gadgets` are **frozen**: bond-cli, the
  coordinator, and the orchestrator consume them across packages.
- Figures and manuscript variables are regenerated, never hand-maintained.
- No mock framework, ever. Deterministic seeds, always.
