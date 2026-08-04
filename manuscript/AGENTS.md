---
title: "Manuscript directory: octopussy — FABERGÉ"
type: "manuscript_guide"
version: "0.1.0"
---

# Manuscript (`projects/working/bond/octopussy/manuscript/`)

This file covers manuscript-specific editing for the FABERGÉ film package:
file roles, the `{{VARIABLE}}` token protocol, figure protocol, and the
section-modification workflow. Repository-wide agent rules live in
[`../docs/agent_instructions.md`](../docs/agent_instructions.md).

## File inventory

| File | Role |
|---|---|
| `00_abstract.md` … `07_scope_and_related_work.md` | Numbered prose sections (tokens resolved at render). |
| `99_references.md` | Pandoc reference div. |
| `config.yaml` | Paper metadata, keywords, render/testing toggles. |
| `config.yaml.example` | Reference copy of all configurable fields. |
| `preamble.md`, `references.bib`, `SYNTAX.md`, `README.md` | Sidecars. |

## {{VARIABLE}} protocol

Numeric and outcome values **must** flow through
`src/octopussy/manuscript_variables.py::generate_variables()` as `{{TOKEN}}`,
never hand-authored in prose. Add a new token to that function, then exercise
`tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`
— it scans only `[0-9]*.md`, so sidecars may show literal `{{TOKEN}}` examples.

## Figures

All figures come from `src/octopussy/figures/` (see `SYNTAX.md`). They are
regenerated, never hand-edited.

## Section modification workflow

1. Change behavior in `src/` and update the relevant section prose.
2. Ensure every `{{TOKEN}}` used is emitted by `generate_variables()`.
3. Re-run `scripts/z_generate_manuscript_variables.py` and the test suite.
