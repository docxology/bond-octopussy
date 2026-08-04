# Introduction

In the 1983 film *Octopussy*, the villain's scheme hides a working nuclear
device inside a Fabergé egg and moves it by circus train across Europe. The
**{{FABERGE_CODENAME}}** mission software operationalizes the three
investigative disciplines the counter-operation demands: tell a forged
treasure from a real one, route a smuggled payload under cover, and find a
device concealed in plain sight.

This package, **{{FABERGE_TITLE}}**, is a BOND-suite film package. It exposes a
deterministic, protocol-conformant mission provider (see the frozen BOND-API
contract) whose *execute* stage runs three pure, infrastructure-free domain
pipelines and returns machine-readable verdicts plus full provenance.

The three disciplines are deliberately independent modules:

- `forgery_detection` — spectral/UV fingerprinting;
- `cover_logistics` — min-cost flow over a rail network;
- `concealment_sweep` — radiation and shape/mass anomaly detection.

Each is implemented with real, deterministic algorithms operating on real
data generated from physically-motivated models — not stubs and not mocks.
The remainder of this manuscript specifies the methodology, reports the
measured outcomes, and documents the reproducibility guarantees.
