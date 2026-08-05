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
`src/octopussy/manuscript_variables.py::generate_variables()` as tokens, never
hand-authored in prose. Add the token to that function *and* reference it from
a numbered section in the same change. Four tests in
`tests/test_manuscript_variables.py` enforce the contract, and all four scan
only `[0-9][0-9]_*.md`, so sidecars such as this file may show literal
placeholder examples:

| Test | Enforces |
|---|---|
| `test_live_token_cross_reference` | No section uses a token the generator does not emit. |
| `test_generated_tokens_are_all_consumed_or_infrastructural` | No generated token goes unreferenced (dead tokens are unreviewed tokens). |
| `test_no_bare_metric_numerals_in_results_prose` | Abstract, results, and conclusion contain no bare numeral outside a code span or a resolved token. |
| `test_bibliography_and_citations_agree` | Every cited key exists in `references.bib`, and every entry is cited. |

Never add a bibliography entry whose details you have not confirmed against a
primary source. An uncheckable citation is worse than a missing one — delete
rather than reshape.

## Figures

All figures come from `src/octopussy/figures/` (see `SYNTAX.md`). They are
regenerated, never hand-edited.

## Section modification workflow

1. Change behavior in `src/` and update the relevant section prose.
2. Ensure every `{{TOKEN}}` used is emitted by `generate_variables()`.
3. Re-run `scripts/z_generate_manuscript_variables.py` and the test suite.
