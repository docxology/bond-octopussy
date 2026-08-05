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
- [ ] **The trace-anachronism regime is untested.** The exhibit's least-modern
      fake is still half modern by weight, so nothing here shows the
      matched-filter channel resolving a few percent of modern material out of
      an otherwise period-correct object — the case that would actually be
      hard. Add such an artifact and measure whether it is still flagged.
- [ ] **Varnish kinetics use a single time constant.** τ is fixed for all
      resins and illumination histories. Parameterize τ per resin and fit it
      jointly with age. (The manuscript claim has already been narrowed: the
      results and scope sections now report the channel as a rejection
      instrument only, with the measured saturation scatter beside every
      verdict.)
- [ ] **Varnish dating saturates and cannot confirm old provenance.** With
      τ = 40 y, a century-old surface sits past three time constants and its
      recovered age scatters wider than the consistency tolerance. Stated in
      the manuscript and measured by `age_recovery_scatter`; removing the
      limitation needs a second observable that does not saturate (e.g. a
      cross-linking or solubility proxy), not a better fit.
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
      two are equal by construction, and since the varnish channel now
      multiplies an exhibit spectrum by a transmittance band for band, a
      divergence would be silently wrong rather than an error.
      `tests/test_mission.py::test_varnish_and_forgery_share_one_band_grid`
      binds them, which closes the silent-failure risk; deriving one grid from
      the other would remove the duplication itself and is still open.
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
