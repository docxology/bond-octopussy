# Results

Executing the FABERGÉ mission (seed {{FABERGE_SEED}}) produces the following
measured outcomes. Every figure below is emitted by the live run; none is
transcribed by hand.

## Results at a glance

| Pipeline | Measured outcome |
|---|---|
| Forgery detection | {{FABERGE_SCREENED_ARTIFACTS}} artifacts screened, {{FABERGE_FLAGGED_FORGERY}} flagged as forged / likely-forged |
| Varnish dating (depth) | fresh coat rejected in {{FABERGE_VARNISH_FAKE_REJECTED_TRIALS}}/{{FABERGE_VARNISH_TRIALS}} realizations; century-old surface scatters by {{FABERGE_VARNISH_GENUINE_STD}} years |
| Cover logistics | cost {{FABERGE_LOGISTICS_COST}} unit-min, makespan {{FABERGE_LOGISTICS_MAKESPAN}} min, slack {{FABERGE_LOGISTICS_SLACK}} min |
| Rolling stock (depth) | {{FABERGE_ROLLING_TRAINSETS}} trainsets over {{FABERGE_ROLLING_MATCHING}} successor links, {{FABERGE_ROLLING_DEADHEAD}} deadhead min |
| Concealment sweep | flagged {{FABERGE_SWEEP_FLAGGED}}, worst {{FABERGE_SWEEP_WORST}} |
| Source localization (depth) | position error {{FABERGE_SOURCE_ERROR_M}} m, positional std {{FABERGE_SOURCE_STD_M}} m |

The table collapses the six pipelines into one line each; the sections below
read each result against its own measured uncertainty, which the table does not
— a headline number without its error bar is not a finding.

## Forgery detection

The deterministic exhibit of {{FABERGE_NUM_ARTIFACTS}} artifacts yields
{{FABERGE_SCREENED_ARTIFACTS}} screened readings, of which
{{FABERGE_FLAGGED_FORGERY}} are flagged as forged or likely-forged. Per
artifact, the disposition and the anachronistic pigments the residual evidence
actually attributes:

| Artifact | Disposition | Score | Anachronistic pigments |
|---|---:|---:|---|
| {{FABERGE_VERDICT_1_ARTIFACT}} | {{FABERGE_VERDICT_1_LEVEL}} | {{FABERGE_VERDICT_1_SCORE}} | {{FABERGE_VERDICT_1_ANACH}} |
| {{FABERGE_VERDICT_2_ARTIFACT}} | {{FABERGE_VERDICT_2_LEVEL}} | {{FABERGE_VERDICT_2_SCORE}} | {{FABERGE_VERDICT_2_ANACH}} |
| {{FABERGE_VERDICT_3_ARTIFACT}} | {{FABERGE_VERDICT_3_LEVEL}} | {{FABERGE_VERDICT_3_SCORE}} | {{FABERGE_VERDICT_3_ANACH}} |
| {{FABERGE_VERDICT_4_ARTIFACT}} | {{FABERGE_VERDICT_4_LEVEL}} | {{FABERGE_VERDICT_4_SCORE}} | {{FABERGE_VERDICT_4_ANACH}} |

The honest period pieces score below the genuine threshold and the detector
attributes *no* modern pigment to them — the attribution is a residual-evidence
finding, not an abundance artifact. The all-modern composition
*{{FABERGE_FORGERY_WORST}}* carries the highest forgery score.

The load-bearing case is *{{FABERGE_BORDERLINE_ARTIFACT}}*, the least-modern
fake in the exhibit: {{FABERGE_BORDERLINE_MODERN_PCT}}% of its mixture by
weight post-dates its claimed year of {{FABERGE_BORDERLINE_YEAR}} — a chalk
ground that is period-correct, and a cadmium yellow plus an acrylic varnish
that are not — and the earliest offending pigment misses that date by just
{{FABERGE_BORDERLINE_GAP_YEARS}} years. It is nonetheless flagged.

"Least modern" is relative to this exhibit and nothing more. Half a mixture is
not a trace: the harder regime, where a few percent of modern material has to
be resolved out of an otherwise period-correct object, is *not* exercised by
the shipped exhibit and this package makes no claim about it. What the exhibit
does establish is narrower — the screen is not relying on the trivial
all-modern signature, since the other fake is wholly modern by weight and this
one is not. Figure @fig:forgery shows the spectral fingerprints and UV
responses that separate the classes.

![Spectral fingerprints of a genuine vs. a forged artifact and their UV
fluorescence responses.](figures/forgery_fingerprints.png){#fig:forgery}

## Varnish ageing (forgery depth)

This channel dates two surfaces drawn from the same exhibit the pigment screen
sees: *{{FABERGE_VARNISH_GENUINE_ARTIFACT}}*, whose natural shellac has been on
the object since its claimed {{FABERGE_VARNISH_CLAIMED}} manufacture, and
*{{FABERGE_VARNISH_FAKE_ARTIFACT}}*, whose acrylic coat the forger applied
recently. Each surface is observed as its unvarnished substrate reflectance
attenuated by the varnish film; the film's transmittance is recovered by
dividing out that reference, and the yellowing kinetics are then inverted for
an age.

Read the two results separately, because they are not equally strong.

**The fresh coat is rejected decisively.** Its true age is
{{FABERGE_VARNISH_FAKE_TRUE_AGE}} years; the fit returns
~{{FABERGE_VARNISH_FAKE_AGE}} years and the verdict is
**{{FABERGE_VARNISH_FAKE_VERDICT}}** at a claimed-era closeness of
{{FABERGE_VARNISH_FAKE_CLOSENESS}}. That is not one lucky draw: re-observing
the same surface under {{FABERGE_VARNISH_TRIALS}} independent noise
realizations gives a spread of only {{FABERGE_VARNISH_FAKE_STD}} years, and
{{FABERGE_VARNISH_FAKE_REJECTED_TRIALS}} of {{FABERGE_VARNISH_TRIALS}}
realizations reject the claimed provenance.

**The century-old surface is not resolved at all.** Its authored true age is
{{FABERGE_VARNISH_TRUE_AGE}} years, the fit returns
~{{FABERGE_VARNISH_GENUINE_AGE}} years, and the single-draw verdict against its
own claim is {{FABERGE_VARNISH_GENUINE_VERDICT}}. That verdict carries no
information, and the ensemble is what shows it: across
{{FABERGE_VARNISH_TRIALS}} realizations of the *same* surface the recovered age
scatters by {{FABERGE_VARNISH_GENUINE_STD}} years, spanning
{{FABERGE_VARNISH_GENUINE_MIN}} to {{FABERGE_VARNISH_GENUINE_MAX}} years; only
{{FABERGE_VARNISH_GENUINE_CONSISTENT_TRIALS}} of {{FABERGE_VARNISH_TRIALS}}
land inside the ±{{FABERGE_VARNISH_TOLERANCE}}-year tolerance; and the ensemble
produces {{FABERGE_VARNISH_GENUINE_VERDICTS_SEEN}} distinct verdicts
({{FABERGE_VARNISH_GENUINE_VERDICT_SPREAD}}) from one genuine object. Every
outcome the classifier can emit is reachable from this surface by measurement
noise alone, so which one the mission seed happens to draw says nothing about
the object.

The cause is physical rather than numerical: the yellowing kinetics saturate,
so past roughly three time constants a further decade of ageing shifts the
spectrum by less than the measurement noise, and the age stops being
identifiable. A false rejection of a genuine object is therefore as available
to this channel as a false confirmation.

The honest summary of this channel is asymmetric: varnish ageing is a rejection
instrument for recently re-varnished surfaces and is not a confirmation
instrument for old ones. It reads film chemistry rather than pigment
composition, so its rejection of the duplicate does not share the pigment
screen's failure mode; but both channels observe the same synthetic exhibit
under the same authored ground truth, so they are independent in *observable*,
not in *sample*.

That asymmetry is a property of the kinetics, not of one dataset. Figure
@fig:varnish sweeps true coating age and shows the recovered age tracking truth
until the film is past roughly three time constants — after which the recovered
age scatters beyond any single reading, which is exactly why the century-old
surface above emits every verdict the classifier can produce.

![Recovered varnish age against true coating age, showing the precision
collapse at saturation.](figures/varnish_scatter.png){#fig:varnish}

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
{{FABERGE_ROLLING_DEPOT_COST}} minutes.

Those trips are a separate scenario from the min-cost flow, so the two
pipelines only bear on each other if something compares them. The mission
computes that comparison and reports it. Each of the
{{FABERGE_COVER_ROUTED_LEGS}} station-to-station legs the flow routes must
appear as a scheduled circus trip — every routed leg is covered:
{{FABERGE_COVER_CORRIDOR_COVERED}} — and the trains the flow needs
({{FABERGE_LOGISTICS_TRAINS}}) must not exceed the trainsets the schedule
fields ({{FABERGE_ROLLING_TRAINSETS}}): {{FABERGE_COVER_FLEET_SUFFICIENT}}.
Both are computed from the live pipeline outputs, and either goes false if the
route or the schedule changes. What the matching proves on its own is only the
fleet size the circus schedule requires; it is these two checks, not the
matching, that tie the cover to the routed plan.

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
