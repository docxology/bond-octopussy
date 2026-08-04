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
