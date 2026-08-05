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
unrelated physics or unrelated mathematics. Disagreement between the two is a
finding. Agreement is evidence only in proportion to the depth module's own
measured uncertainty, which is why the results section reports an error bar
beside every depth verdict rather than the verdict alone.

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

It matters asymmetrically, though, and that asymmetry is a result rather than a
caveat. Varnish dating is sharp against a recent film and blunt against an old
one, because the yellowing kinetics saturate; the rolling-stock matching bounds
the circus fleet but says nothing about the routed plan until the two are
explicitly compared. Both facts are measured and reported below. Both pipelines
also read the *same* synthetic scenario, so what the pairing establishes is
independence of observable, not independence of sample.

Every module is implemented with real, deterministic algorithms operating on
data generated from physically-motivated forward models — not stubs and not
mocks. The remainder of this manuscript specifies the methodology, reports the
measured outcomes, and documents the reproducibility guarantees.
