# Manuscript · Octopussy: FABERGÉ

Forensics, logistics, and device-sweep manuscript for the FABERGÉ film
package. The numbered `NN_*.md` sections are templates whose `{{TOKEN}}`s are
resolved by `scripts/z_generate_manuscript_variables.py` into
`output/manuscript/`; the live source of truth for tokens is
`src/octopussy/manuscript_variables.py`.

- `config.yaml` — paper metadata, keywords, render/testing toggles.
- `config.yaml.example` — reference copy of every configurable field.
- `references.bib` — BibTeX bibliography.
- `SYNTAX.md` — citation/figure/token syntax reference.

Regenerate the resolved manuscript and figures with:

```bash
uv run python scripts/z_generate_manuscript_variables.py
```
