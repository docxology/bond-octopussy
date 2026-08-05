# COUNTS — Octopussy: FABERGÉ (regenerated)

> Generated counts — **do not hardcode these elsewhere**; regenerate after the
> suite changes. Source of truth: `uv run pytest tests/ --cov=src`.
> Every figure below was read off a real run, never estimated.

| Metric | Value | As of |
|---|---|---|
| Tests passed | 155 | 2026-08-05 |
| Tests failed / skipped | 0 / 0 | 2026-08-05 |
| Line+branch coverage on `src/` | 97.43 % | 2026-08-05 |
| Coverage gate (`--cov-fail-under`) | 90 % | — |
| Pure domain modules | 6 | — |
| Mission pipelines (`mission.PIPELINE_COUNT`) | 6 | — |
| Mock frameworks in use | 0 | — |

## Per-module coverage (same run)

| Module | Coverage |
|---|---|
| `concealment_sweep.py` | 100.00 % |
| `varnish_ageing.py` | 100.00 % |
| `mission.py` | 100.00 % |
| `manuscript_variables.py` | 100.00 % |
| `figures/forgery.py` | 100.00 % |
| `figures/logistics.py` | 100.00 % |
| `figures/sweep.py` | 100.00 % |
| `forgery_detection.py` | 97.96 % |
| `rolling_stock.py` | 96.54 % |
| `source_locator.py` | 93.62 % |
| `cover_logistics.py` | 93.31 % |

The two lowest modules are tracked in [`../../TODO.md`](../../TODO.md): their
uncovered lines are defensive paths in the augmenting-path search and the
Gauss–Newton line search — comfortably above the gate, but exactly the paths
that run when something goes wrong.

Regenerate with:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```
