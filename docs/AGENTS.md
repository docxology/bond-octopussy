---
title: "docs: octopussy — FABERGÉ"
type: "documentation_guide"
version: "0.1.0"
---

# Docs (octopussy)

Agent-facing docs for the FABERGÉ film package. Keep this directory in sync
with `src/` and `scripts/`; regenerate derived numbers (e.g. coverage) into
`_generated/` rather than hand-editing.

## Files

- `agent_instructions.md` — scope, hard rules, gates, verification checklist.
- `architecture.md` — layer diagram, domain module map, boundaries.
- `testing_philosophy.md` — no-mocks determinism doctrine and test layout.
- `_generated/COUNTS.md` — live test count + coverage (regenerated, never
  hand-authored literals in prose).

See `../docs/agent_instructions.md` and `../AGENTS.md` for repo-wide rules.
