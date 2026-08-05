# Methodology

The mission's three pipelines share a design principle: every quantity that
reaches a verdict is *measured* or *computed*, never assumed, and every random
draw is seeded so the entire pipeline reproduces byte-for-byte under a fixed
seed ({{FABERGE_SEED}}).

## Spectral/UV forgery detection

A painted artifact is modeled as a weighted mixture of pigments, each with a
known reflectance curve over a {{FABERGE_NUM_PIGMENTS}}-strong library of 24
UV-VIS bands. The instrument observes a noised reflectance spectrum and a
noised UV-fluorescence reading; it never sees the true composition.

Three evidence channels are combined:

1. **Anachronism (matched filter + residual improvement).** A
   ridge-regularized non-negative least-squares fit reconstructs the spectrum
   using only era-consistent pigments; the residual (the signal no
   era-consistent pigment explains) is matched against each anachronistic
   pigment's distinctive shape. Strong alignment — or a large shrink in
   residual when modern pigments are allowed — is direct evidence of a modern
   forgery.
2. **UV fluorescence anomaly.** Aged shellac fluoresces weakly; young
   synthetic varnishes fluoresce brightly. A reading well above the shellac
   baseline signals a modern surface.
3. **Unexplained spectral residue.** A high era-consistent residual with
   small explained variance indicates a surface no legal composition can
   reproduce.

The three channels are weighted and mapped to a disposition:
*genuine / likely_genuine / likely_forged / forged*.

## Circus-cover logistics (min-cost flow)

The corridor is a directed rail graph whose segments carry integer travel
costs and capacities. Routing the payload from source to sink is a minimum-cost
flow problem solved by successive shortest paths (Bellman-Ford augmenting
paths), then decomposing the flow into per-unit routes to obtain a makespan. A
deadline check yields slack, and the payload is packed into circus trains of
fixed wagon capacity.

## Concealed-device sweep

Each detector observes a Poisson count rate equal to a background plus the
inverse-square contributions of any emitters. A median-filtered background
estimate yields a Poisson-normalized z-score map, and local-maximum peaks above
threshold are reported as hotspots. In parallel, each cargo container's mass is
judged against its category's expected density; a container far heavier than
its volume allows carries a mass anomaly. A fused report ranks both channels
into one prioritized suspicion list.

## Varnish-ageing kinetics (forgery depth)

Natural resin varnishes yellow over time. The module models this with a
saturating exponential law: the absorbing layer grows as
``d(t) = d_max·(1 − exp(−t/τ))`` and the film's transmittance follows
Beer–Lambert, ``T(λ, t) = exp(−α(λ)·d(t))``, with a blue-peaked absorption
spectrum ``α(λ)``. The inverse problem — *given a measured transmittance, how
old is the varnish?* — is solved by a bounded golden-section least-squares fit
over the age axis (derivative-free, deterministic). An object whose varnish
is far younger than its claimed provenance is a repaint or re-varnish, a
standalone forgery signal.

## Rolling-stock circulation (logistics depth)

Beyond routing the payload, the mission must know how many circus trainsets
the schedule truly needs. Treating each trip as a node with a directed edge
``i → j`` when a trainset can work ``j`` after ``i`` (same intermediate
station, ``depart_j ≥ arrive_i + turnaround``), the minimum number of
trainsets equals ``n − M`` where ``M`` is the maximum bipartite matching
(minimum path cover theorem) — computed deterministically with Hopcroft–Karp.
The matching is decomposed into concrete trainset itineraries, and a
Kuhn–Munkres minimum-cost assignment resolves depot allocation with the
minimum total deadhead.

## Radiation source localization (sweep depth)

Given the detector lattice and a Poisson background estimate, the concealed
emitter is located by weighted nonlinear least squares. With forward model
``μ_i = B + I/((x_i−x)² + (y_i−y)² + h²)`` and weights
``w_i = 1/√max(c_i, 1)``, Gauss–Newton iteration with damped normal equations
and a deterministic line search minimizes the weighted residual; an
excess-weighted-centroid start keeps the solver seed-free. The inverse normal
matrix yields an approximate positional and intensity uncertainty.
