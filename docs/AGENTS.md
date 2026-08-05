---
title: "docs: octopussy — FABERGÉ"
type: "documentation_guide"
version: "0.1.0"
---

# Docs directory (octopussy)

Rules for editing `projects/working/bond/octopussy/docs/`. Package-wide agent
rules live in [`agent_instructions.md`](agent_instructions.md); repository-wide
rules live in [`../AGENTS.md`](../AGENTS.md).

## File inventory

| File | Owner of |
|---|---|
| `README.md` | The index of this directory and the pointers out of it. |
| `agent_instructions.md` | Hard rules, scope boundary, gates, verification checklist. |
| `architecture.md` | The six domain modules, the mission adapter, the layer boundaries. |
| `testing_philosophy.md` | No-mock doctrine, determinism enforcement, test-file map. |
| `AGENTS.md` | This file. |
| `_generated/COUNTS.md` | Measured test count and coverage. **Generated.** |

## Rules

1. **Describe the code that exists.** Every module named in `architecture.md`
   must exist in `src/octopussy/`, and every module in `src/octopussy/` must
   appear there. When you add or delete a module, the same change updates
   `architecture.md`, `testing_philosophy.md`'s test map, the root
   `README.md`, and `../AGENTS.md`'s layer-contract table. Four sites; a
   partial update is how doc drift starts.
2. **Never hand-write a measured number.** Test counts, coverage percentages,
   and mission outcomes belong in `_generated/COUNTS.md` (regenerated) or in a
   manuscript token (injected). In prose here, describe the *gate* — "≥90%
   branch coverage on `src/`, enforced by `--cov-fail-under=90`" — not the
   figure it currently reports.
3. **`_generated/` is output.** Regenerate it from a real run; never edit a
   number in it by hand, and never quote one of its numbers into another file.
4. **No exemplar boilerplate.** This package was forked from the template
   exemplar `template_code_project`; that lineage may be mentioned, but no
   text describing the exemplar's own domain may survive here.
5. **Cross-references must resolve.** Relative links are checked by eye at
   review time — if you move a file, fix the links pointing at it.

## When docs and code disagree

The code wins, and the doc is the defect. Fix the doc in the same commit that
revealed the mismatch; do not open a follow-up item for it.
