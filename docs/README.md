# Docs — Octopussy: FABERGÉ

Agent-facing documentation for the FABERGÉ film package (BOND suite, film
*Octopussy*, 1983). This directory explains how the package is built, how to
work inside it, and what its quality gates actually mean. It is prose about
*this* package — none of it is exemplar boilerplate, and none of it restates a
measured number that could go stale.

## What's here

| File | Read it when you need |
|---|---|
| [`agent_instructions.md`](agent_instructions.md) | The operating rules: scope boundary, layer purity, determinism, and the verification checklist to clear before claiming done. **Start here.** |
| [`architecture.md`](architecture.md) | Module-by-module map of `src/octopussy/` — what each of the six domain modules computes, how they compose, and exactly how `mission.py` implements the frozen `bond_api.MissionProvider`. |
| [`testing_philosophy.md`](testing_philosophy.md) | Why there are no mocks, what "deterministic" is enforced to mean here, which test file covers what, and the anti-vacuity rules a new test must satisfy. |
| [`AGENTS.md`](AGENTS.md) | Rules for editing *this docs directory* specifically. |
| [`_generated/COUNTS.md`](_generated/COUNTS.md) | The live measured test count and coverage. Regenerated, never hand-edited — treat any number there as valid only as of its stated date, and re-run the gate rather than quoting it. |

## Reading order

1. `agent_instructions.md` — the constraints you must not violate.
2. `architecture.md` — what exists and where the boundaries fall.
3. `testing_philosophy.md` — how to add code without weakening the suite.

## Documented elsewhere

- **Package overview, film→software mapping, quick start** — [`../README.md`](../README.md).
- **Build/test/verify command reference** — [`../AGENTS.md`](../AGENTS.md).
- **Remaining work** — [`../TODO.md`](../TODO.md).
- **Manuscript token protocol, figure protocol, section workflow** —
  [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) and
  [`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md).
- **The frozen cross-package protocol itself** — the sibling `bond-api`
  package (`bond_api.protocol`), which this package consumes and must not
  modify.
