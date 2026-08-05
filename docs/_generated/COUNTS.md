# COUNTS — Octopussy: FABERGÉ (regenerated)

> Generated counts — **do not hardcode** these elsewhere; regenerate after the
> suite changes. Source of truth: `uv run pytest tests/ --cov=src`.

| Metric | Value | As of |
|---|---|---|
| Tests passed | 119 | 2026-08-04 |
| Line+branch coverage on `src/` | 97.17 % | 2026-08-04 |
| Coverage gate (`--cov-fail-under`) | 90 % | — |
| Pure domain modules | 6 | — |

Regenerate with:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```
