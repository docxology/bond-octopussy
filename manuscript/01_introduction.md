# Introduction

In the 1983 film *Octopussy*, the villain's scheme hides a working nuclear
device inside a Fabergé egg and moves it by circus train across Europe. The
**{{FABERGE_CODENAME}}** mission software operationalizes the three
investigative disciplines the counter-operation demands: tell a forged
treasure from a real one, route a smuggled payload under cover, and find a
device concealed in plain sight.

This package, **{{FABERGE_TITLE}}**, is a BOND-suite film package. It exposes a
deterministic, protocol-conformant mission provider (see the frozen BOND-API
contract) whose *execute* stage runs {{FABERGE_NUM_PIPELINES}} pure,
infrastructure-free domain pipelines and returns machine-readable verdicts
plus full provenance.

## Three disciplines, {{FABERGE_NUM_PIPELINES}} pipelines

The governing design decision is that no single detector carries a verdict
alone. Each discipline is implemented twice: a *headline* module that raises
the alarm, and a *depth* module that reaches the same question through
unrelated physics or unrelated mathematics. Agreement between the two is the
evidence; disagreement is itself a finding.

| Discipline | Headline module | Depth module |
|---|---|---|
| Is this object what it claims to be? | `forgery_detection` — spectral/UV fingerprinting | `varnish_ageing` — Beer–Lambert yellowing kinetics |
| Can the payload move under cover? | `cover_logistics` — min-cost flow over the rail corridor | `rolling_stock` — trainset circulation by bipartite matching |
| Is a device hidden here, and where? | `concealment_sweep` — radiation + shape/mass anomaly fusion | `source_locator` — weighted Gauss–Newton localization |

The pairing matters operationally. Pigment chemistry and varnish kinetics fail
in different directions: a forger who sources period-correct pigments still
cannot age a fresh varnish film, while a genuinely old panel that was recently
restored trips the varnish channel although the pigment channel clears it.
Likewise, a routing plan that satisfies capacity says nothing about whether
enough trainsets exist to fly the cover at all, and a sweep that flags a
container has not yet said where inside the yard the emitter sits.

Every module is implemented with real, deterministic algorithms operating on
data generated from physically-motivated forward models — not stubs and not
mocks. The remainder of this manuscript specifies the methodology, reports the
measured outcomes, and documents the reproducibility guarantees.
