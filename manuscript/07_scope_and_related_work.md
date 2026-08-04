# Scope and related work

**Scope.** This package models the three FABERGÉ disciplines with
deterministic, real-data implementations. It does not claim physical
fidelity to real forensic spectrometers, real rail networks, or real
scintillation detectors; the underlying models are physically motivated but
illustrative. The pigment library, corridor, and container catalog are
deterministic fixtures, not measured instrumentation.

**Related work.** Non-negative least-squares spectral unmixing and matched
filtering are standard in hyperspectral remote sensing and cultural-heritage
science for pigment identification; this package applies the same mathematics
to the anachronism test. Minimum-cost flow via successive shortest paths is a
classical combinatorial-optimization result. Poisson background estimation
with z-score anomaly detection is standard in radiation portal monitoring.
The contribution here is the assembly of these primitives behind a single
frozen mission protocol with deterministic, audit-ready provenance.
