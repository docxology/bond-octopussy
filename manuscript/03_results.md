# Results

Executing the FABERGÉ mission (seed {{FABERGE_SEED}}) produces the following
measured outcomes. Every figure below is emitted by the live run; none is
transcribed by hand.

## Forgery detection

The deterministic exhibit of {{FABERGE_NUM_ARTIFACTS}} artifacts yields
{{FABERGE_SCREENED_ARTIFACTS}} screened readings, of which
{{FABERGE_FLAGGED_FORGERY}} are flagged as forged or likely-forged. The honest
period pieces score below the genuine threshold; the all-modern composition
*{{FABERGE_FORGERY_WORST}}* carries the highest forgery score.

The load-bearing case is *{{FABERGE_BORDERLINE_ARTIFACT}}*, the least-modern
fake in the exhibit: only {{FABERGE_BORDERLINE_MODERN_PCT}}% of its mixture by
weight post-dates its claimed year of {{FABERGE_BORDERLINE_YEAR}}, and the
earliest offending pigment misses that date by just
{{FABERGE_BORDERLINE_GAP_YEARS}} years. It is nonetheless flagged. That is the
substantive claim: an all-modern composition would be caught by any channel,
whereas this one is mostly period-correct and is resolved by the matched-filter
anachronism evidence against a minority of modern material. Figure @fig:forgery
shows the spectral fingerprints and UV responses that separate the classes.

![Spectral fingerprints of a genuine vs. a forged artifact and their UV
fluorescence responses.](figures/forgery_fingerprints.png){#fig:forgery}

## Varnish ageing (forgery depth)

Dating the same exhibit's varnish by yellowing kinetics, the genuine surface
measures about {{FABERGE_VARNISH_GENUINE_AGE}} years —
{{FABERGE_VARNISH_GENUINE_VERDICT}} with the claimed
{{FABERGE_VARNISH_CLAIMED}} provenance. The freshly varnished duplicate dates
to just ~{{FABERGE_VARNISH_FAKE_AGE}} years and is rejected as
**{{FABERGE_VARNISH_FAKE_VERDICT}}**, at a claimed-era closeness of
{{FABERGE_VARNISH_FAKE_CLOSENESS}}: its surface is decades younger than it
claims to be. Because this channel reads varnish chemistry rather than pigment
composition, it corroborates the forgery screen without sharing its failure
mode.

## Cover logistics

Routing {{FABERGE_LOGISTICS_UNITS}} payload units across the
{{FABERGE_NUM_SEGMENTS}}-segment, {{FABERGE_NUM_STATIONS}}-station corridor
from the Channel fringe to the target station, the min-cost flow resolves at a
total cost of {{FABERGE_LOGISTICS_COST}} unit-minutes with a makespan of
{{FABERGE_LOGISTICS_MAKESPAN}} minutes. Against the
{{FABERGE_LOGISTICS_DEADLINE}}-minute deadline that leaves
{{FABERGE_LOGISTICS_SLACK}} minutes of slack, carried by
{{FABERGE_LOGISTICS_TRAINS}} circus trains at the capacity limit. Figure
@fig:rail plots the corridor and the routed flow.

![The FABERGÉ circus rail corridor with routed flow.](figures/rail_network.png){#fig:rail}

## Rolling-stock circulation (logistics depth)

The schedule of {{FABERGE_ROLLING_TRIPS}} circus trips requires only
{{FABERGE_ROLLING_TRAINSETS}} trainsets: a maximum successor matching of
{{FABERGE_ROLLING_MATCHING}} links (minimum path cover) resolves the
itineraries with {{FABERGE_ROLLING_DEADHEAD}} total deadhead minutes. The
Kuhn–Munkres depot allocation reaches a minimum total of
{{FABERGE_ROLLING_DEPOT_COST}} minutes. The cover is therefore not merely
routable but *staffable* — the corridor plan above does not exceed the
trainsets the troupe can actually field.

## Concealment sweep

The {{FABERGE_NUM_DETECTORS}}-detector sweep, laid out as a
{{FABERGE_GRID_NX}}×{{FABERGE_GRID_NY}} lattice, flags
{{FABERGE_SWEEP_FLAGGED}}. The fused report ranks {{FABERGE_SWEEP_WORST}}
highest across {{FABERGE_NUM_CONTAINERS}} screened containers, confirming a
dense sample egg as a flagged mass anomaly — the Fabergé-egg signature of a
small, dense concealed core. Figure @fig:sweep renders the radiation count map
with the detected hotspot.

![Concealed-device sweep: radiation count rates with the detected hotspot.](figures/sweep_heatmap.png){#fig:sweep}

## Source localization (sweep depth)

Weighted Gauss–Newton localization on the same sweep data recovers the
concealed source to within **{{FABERGE_SOURCE_ERROR_M}} m** of its true
position in {{FABERGE_SOURCE_ITERATIONS}} iterations, estimating an intensity
of {{FABERGE_SOURCE_INTENSITY}} and a weighted residual of
{{FABERGE_SOURCE_RESIDUAL}} (converged: {{FABERGE_SOURCE_CONVERGED}}). The
fit's own approximate positional standard deviation is
{{FABERGE_SOURCE_STD_M}} m, so the achieved error is reported against the
precision the detector geometry supports rather than in isolation. The sweep
therefore both flags the device and fixes where it sits.

The intensity estimate is a different matter and should not be read as a
calibrated activity. Against a true emitter strength of
{{FABERGE_SOURCE_TRUE_INTENSITY}} the fit returns
{{FABERGE_SOURCE_INTENSITY}} — a substantial underestimate, while the position
is recovered to centimetres. This is expected rather than anomalous:
intensity, standoff, and the background level trade off against one another in
an inverse-square fit, so the radial scale is poorly constrained by a
single-plane lattice even when the centroid is sharp. The operational claim is
therefore *where the source is*, not *how strong it is*.
