# Methodology

The mission's {{FABERGE_NUM_PIPELINES}} pipelines share a design principle:
every quantity that reaches a verdict is *measured* or *computed*, never
assumed, and every random draw is seeded so the entire pipeline reproduces
byte-for-byte under a fixed seed ({{FABERGE_SEED}}).

## Spectral/UV forgery detection

A painted artifact is modeled as a weighted mixture drawn from a library of
{{FABERGE_NUM_PIGMENTS}} pigments, each with a known reflectance curve over
{{FABERGE_NUM_BANDS}} UV-VIS bands spanning
{{FABERGE_BAND_MIN_NM}}–{{FABERGE_BAND_MAX_NM}} nm. The instrument observes a
noised reflectance spectrum and a noised UV-fluorescence reading; it never
sees the true composition.

Recovering pigment abundances from a mixed reflectance spectrum is the
spectral-unmixing problem of hyperspectral remote sensing
[@keshava2002spectral], solved here in its non-negative least-squares form
[@lawson1974solving] with a ridge penalty, because the flat "white" pigments
are strongly collinear and an unregularized fit spreads weight arbitrarily
between them.

Three evidence channels are combined:

1. **Anachronism (matched filter + residual improvement).** A
   ridge-regularized non-negative least-squares fit reconstructs the spectrum
   using only era-consistent pigments; the residual — the signal no
   era-consistent pigment explains — is matched against each anachronistic
   pigment's distinctive shape. Strong alignment, or a large shrink in the
   residual when modern pigments are allowed, is direct evidence of a modern
   forgery. Both statistics are deliberately computed from the residual rather
   than from individual fitted weights, which collinearity makes unreliable.
2. **UV fluorescence anomaly.** Aged natural-resin varnish fluoresces weakly;
   young synthetic varnishes fluoresce brightly — the observation underlying
   routine UV examination of paint and varnish layers
   [@delarie1982fluorescence]. A reading well above the shellac baseline
   signals a modern surface.
3. **Unexplained spectral residue.** A high era-consistent residual with small
   explained variance indicates a surface no period-legal composition can
   reproduce.

The three channels are weighted and mapped to a disposition:
*genuine / likely_genuine / likely_forged / forged*. The thresholds are
empirical calibrations against the deterministic exhibit's measured score
separation, not free parameters.

## Varnish-ageing kinetics (forgery depth)

Natural resin varnishes yellow over time as photochemical and thermal
degradation accumulates chromophores in the film [@feller1994accelerated;
@horie2010materials]. The module represents this with a saturating exponential
law: the absorbing layer grows as `d(t) = d_max·(1 − exp(−t/τ))` and the
film's transmittance follows Beer–Lambert, `T(λ, t) = exp(−α(λ)·d(t))`, with a
blue-peaked absorption spectrum `α(λ)`. The inverse problem — *given a measured
transmittance, how old is the varnish?* — is solved by a bounded
golden-section least-squares fit over the age axis [@kiefer1953sequential]:
derivative-free, deterministic, and independent of any starting guess. An
object whose varnish is far younger than its claimed provenance is a repaint
or re-varnish — a standalone forgery signal that does not depend on the
pigment screen agreeing.

## Circus-cover logistics (min-cost flow)

The corridor is a directed rail graph of {{FABERGE_NUM_STATIONS}} stations and
{{FABERGE_NUM_SEGMENTS}} segments carrying integer travel costs and
capacities. Routing the payload from source to sink is a minimum-cost flow
problem [@ahuja1993network; @ford1962flows] solved by successive shortest
paths. Augmenting paths are found with Bellman–Ford [@bellman1958routing]
rather than Dijkstra, because cancelling previously-shipped flow along a
reverse arc carries negative reduced cost. The flow is then decomposed into
per-unit routes to obtain a makespan, a deadline check yields slack, and the
payload is packed into circus trains of fixed wagon capacity. A least-cost
single-courier route is available separately by Dijkstra [@dijkstra1959note].

Feasibility is reported, never assumed: the flow solver raises when the
corridor cannot carry the demand, and the non-raising planner surfaces that as
a plan marked infeasible with zero routed edges and the full deadline missed.

## Rolling-stock circulation (logistics depth)

Beyond routing the payload, the mission must know how many circus trainsets
the schedule truly needs. Treating each trip as a node with a directed edge
`i → j` when a trainset can work `j` after `i` (matching stations,
`depart_j ≥ arrive_i + turnaround`), the minimum number of trainsets equals
`n − M`, where `M` is the maximum bipartite matching — the minimum-path-cover
form of the classical minimum-fleet-size result [@dantzig1954minimizing], and a
standard reduction in train-timetabling practice [@caprara2002train]. The
matching is computed deterministically with Hopcroft–Karp
[@hopcroft1973matching], decomposed into concrete trainset itineraries, and a
Kuhn–Munkres minimum-cost assignment [@kuhn1955hungarian] resolves depot
allocation at minimum total deadhead.

## Concealed-device sweep

Each detector observes a Poisson count rate equal to a background plus the
inverse-square contributions of any emitters — the standard counting model for
scintillation detection [@knoll2010radiation]. A median-filtered background
estimate yields a Poisson-normalized z-score map, and local-maximum peaks above
threshold are reported as hotspots; that threshold is a detection decision
level in the sense of Currie [@currie1968limits]. In parallel, each cargo
container's mass is judged against its category's expected density from a
catalog of {{FABERGE_NUM_CATEGORIES}} physical profiles; a container far
heavier than its volume allows carries a mass anomaly — the signature of a
small dense core inside an ordinary-looking shell. A fused report ranks both
channels into one prioritized suspicion list.

## Radiation source localization (sweep depth)

Flagging a hotspot is not the same as finding the device. Given the detector
lattice and a Poisson background estimate, the concealed emitter is located by
weighted nonlinear least squares. With forward model
`μ_i = B + I/((x_i−x)² + (y_i−y)² + h²)` and weights `w_i = 1/√max(c_i, 1)`,
Gauss–Newton iteration with damped normal equations [@marquardt1963algorithm;
@nocedal2006numerical] and a deterministic step-halving line search minimizes
the weighted residual; an excess-weighted-centroid start keeps the solver
seed-free and reproducible. Inverting the normal matrix yields approximate
positional and intensity standard deviations, so a reported fix always ships
with the precision that justifies it.
