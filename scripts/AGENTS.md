---
title: "scripts: octopussy — FABERGÉ"
type: "scripts_guide"
version: "0.1.0"
---

# scripts (octopussy)

Thin orchestrators only. Rules:

- Business logic belongs in `src/octopussy/`, never here.
- Bootstrap `src/` with a `sys.path.insert` before local imports and mark those
  import lines with `# noqa: E402` (deep monorepo path — the root per-file
  ignore does not cover `projects/working/bond/<pkg>/scripts/`).
- Deterministic: no wall-clock writes; write regenerable artifacts under
  `output/`.
- Subprocess smoke tests run these with `sys.executable` and `cwd=project_root`.

Add a script only when a mission phase or a regeneration step genuinely needs
a CLI. See `CONVENTIONS.md` and `README.md`.
