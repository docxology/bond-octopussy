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

Three limits follow and should be read with the results:

- **The exhibit is small and self-authored.** Separation between classes is
  measured on {{FABERGE_NUM_ARTIFACTS}} artifacts drawn from the same library
  the detector fits against; it is a demonstration of the method's mechanics,
  not an estimate of field accuracy. There is no genuine period piece using a
  pigment near the anachronism boundary, so the false-positive rate is
  untested.
- **The varnish kinetics use one time constant.** Real varnish ageing depends
  on resin, illumination history, and storage; a single τ is a first-order
  stand-in, and the absolute ages should be read as consistency checks against
  a claimed provenance rather than as datings.
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
frozen mission protocol, with deterministic and audit-ready provenance.
