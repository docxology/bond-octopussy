# Results

Executing the FABERGÉ mission (seed {{FABERGE_SEED}}) produces the following
measured outcomes.

## Forgery detection

The deterministic exhibit of {{FABERGE_NUM_ARTIFACTS}} artifacts screens to
{{FABERGE_FLAGGED_FORGERY}} flagged as forged or likely-forged. The two honest
period pieces score below the genuine threshold; the all-modern composition
*{{FABERGE_FORGERY_WORST}}* carries the highest forgery score, and the
borderline 1888 piece with a 22-year-anachronistic pigment and a modern
varnish is flagged as likely-forged. Figure @fig:forgery shows the spectral
fingerprints and UV responses that separate the classes.

![Spectral fingerprints of a genuine vs. a forged artifact and their UV
fluorescence responses.](figures/forgery_fingerprints.png){#fig:forgery}

## Cover logistics

Routing {{FABERGE_NUM_SEGMENTS}} rail segments from the Channel fringe to the
target station, the min-cost flow resolves with a makespan of
{{FABERGE_LOGISTICS_MAKESPAN}} minutes and a schedule slack of 140 minutes for
the stated deadline, using {{FABERGE_LOGISTICS_TRAINS}} circus trains at the
capacity limit. Figure @fig:rail plots the corridor and the routed flow.

![The FABERGÉ circus rail corridor with routed flow.](figures/rail_network.png){#fig:rail}

## Concealment sweep

The {{FABERGE_NUM_DETECTORS}}-detector sweep flags {{FABERGE_SWEEP_FLAGGED}}.
The fused report ranks the radiation hotspot highest and confirms a dense
sample egg as a flagged mass anomaly — the Fabergé-egg signature of a small,
dense concealed core. Figure @fig:sweep renders the radiation count map with
the detected hotspot.

![Concealed-device sweep: radiation count rates with the detected hotspot.](figures/sweep_heatmap.png){#fig:sweep}
