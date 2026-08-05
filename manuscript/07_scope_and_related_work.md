# Scope and related work

## Scope

This package models the three FABERGÉ disciplines with deterministic,
real-data implementations across {{FABERGE_NUM_PIPELINES}} pipelines. It does
**not** claim physical fidelity to real forensic spectrometers, real rail
networks, or real scintillation detectors: the underlying models are
physically motivated but illustrative. The
{{FABERGE_NUM_PIGMENTS}}-pigment library, the
{{FABERGE_NUM_SEGMENTS}}-segment corridor, and the
{{FABERGE_NUM_CATEGORIES}}-category container catalog are deterministic
fixtures, not measured instrumentation.

These limits follow and should be read with the results:

- **The exhibit is small and self-authored.** Separation between classes is
  measured on {{FABERGE_NUM_ARTIFACTS}} artifacts drawn from the same library
  the detector fits against; it is a demonstration of the method's mechanics,
  not an estimate of field accuracy. There is no genuine period piece using a
  pigment near the anachronism boundary, so the false-positive rate is
  untested.
- **The hard anachronism regime is not exercised.** The exhibit's least-modern
  fake is still {{FABERGE_BORDERLINE_MODERN_PCT}}% modern by weight. Nothing
  here speaks to resolving a trace of modern material out of an otherwise
  period-correct object, which is the case that would actually test the
  matched-filter channel.
- **Ground truth is authored, so these are estimator results.** Every number
  reported here is measured on a synthetic scenario defined in this package —
  the pigment mixtures, the true varnish ages, the emitter position, the rail
  schedule. The results characterize how the estimators behave against a known
  truth; they are not measurements of any physical object, and headline and
  depth modules share that one scenario. The pairing gives independence of
  observable, not independence of sample.
- **The varnish kinetics use one time constant, and they saturate.** Real
  varnish ageing depends on resin, illumination history, and storage; a single
  τ is a first-order stand-in. More consequentially, the saturating exponential
  means that past roughly three time constants a further decade of ageing moves
  the spectrum by less than the measurement noise. As the results section
  reports, the recovered age of the {{FABERGE_VARNISH_TRUE_AGE}}-year surface
  scatters by {{FABERGE_VARNISH_GENUINE_STD}} years across
  {{FABERGE_VARNISH_TRIALS}} noise realizations — wider than the
  ±{{FABERGE_VARNISH_TOLERANCE}}-year tolerance it is judged against, and wide
  enough to emit {{FABERGE_VARNISH_GENUINE_VERDICTS_SEEN}} distinct verdicts
  from that one genuine object. This channel can reject a recent re-varnish; on
  an old surface it produces a verdict with no information content, in either
  direction, and none of its old-surface verdicts should be reported as
  evidence.
- **The two cover pipelines are linked by an explicit check, not by
  construction.** The circus schedule is a fixture independent of the min-cost
  flow. The results section reports two computed comparisons that connect them;
  absent those, the matching would bound the circus fleet and say nothing at all
  about the routed corridor plan.
- **The sweep model is idealized.** Counts are Poisson about an inverse-square
  field with no scattering, no attenuation through cargo, and no
  energy-resolved spectroscopy — the discriminants a real portal monitor
  depends on most.
- **Localized intensity is not calibrated activity.** As the results show, the
  fit recovers position to centimetres while substantially underestimating
  emitter strength: intensity, standoff, and background trade off in an
  inverse-square model, and a single-plane detector lattice constrains the
  radial scale weakly. Read the localization output as a position, not as a
  source-strength measurement.

## Related work

Non-negative least-squares spectral unmixing [@lawson1974solving] and matched
filtering are standard in hyperspectral remote sensing
[@keshava2002spectral] and, in the reflectance regime, in cultural-heritage
science for pigment identification; this package applies the same mathematics
to the anachronism test. UV examination of varnish fluorescence is long-
established conservation practice [@delarie1982fluorescence], and the ageing
behaviour of natural resin films is documented in the conservation-materials
literature [@feller1994accelerated; @horie2010materials].

Minimum-cost flow via successive shortest paths is a classical
combinatorial-optimization result [@ford1962flows; @ahuja1993network] built on
the shortest-path algorithms of Bellman [@bellman1958routing] and Dijkstra
[@dijkstra1959note]. Deriving a minimum fleet size from a maximum matching
goes back to Dantzig and Fulkerson [@dantzig1954minimizing] and remains the
standard reduction in railway timetabling [@caprara2002train]; the matching
itself is Hopcroft–Karp [@hopcroft1973matching] and the depot assignment is
Kuhn's Hungarian method [@kuhn1955hungarian].

Poisson background estimation with z-score anomaly detection is standard in
radiation portal monitoring [@knoll2010radiation], with decision thresholds in
the tradition of Currie [@currie1968limits]; damped Gauss–Newton inversion for
source parameters follows standard nonlinear least-squares practice
[@marquardt1963algorithm; @nocedal2006numerical].

The contribution here is not any individual algorithm but the assembly: each
discipline answered by two methods with disjoint failure modes, behind a single
frozen mission protocol, with deterministic and audit-ready provenance — and
with each depth method reporting the uncertainty that determines how much its
agreement is worth.
