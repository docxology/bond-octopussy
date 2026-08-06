# COUNTS — Octopussy: FABERGÉ (regenerated)

> Generated counts — **do not hardcode these elsewhere**; regenerate after the
> suite changes. Source of truth: `uv run pytest tests/ --cov=src`.
> Every figure below was read off a real run, never estimated.

| Metric | Value | As of |
|---|---|---|
| Tests passed | 168 | 2026-08-06 |
| Tests failed / skipped | 0 / 0 | 2026-08-06 |
| Line+branch coverage on `src/` | 99.36 % | 2026-08-06 |
| Coverage gate (`--cov-fail-under`) | 90 % | — |
| Pure domain modules | 6 | — |
| Mission pipelines (`mission.PIPELINE_COUNT`) | 6 | — |
| Mock frameworks in use | 0 | — |

## Per-module coverage (same run)

| Module | Coverage |
|---|---|
| `_bands.py` | 100.00 % |
| `concealment_sweep.py` | 100.00 % |
| `varnish_ageing.py` | 100.00 % |
| `mission.py` | 100.00 % |
| `manuscript_variables.py` | 100.00 % |
| `figures/forgery.py` | 100.00 % |
| `figures/logistics.py` | 100.00 % |
| `figures/sweep.py` | 100.00 % |
| `figures/varnish.py` | 100.00 % |
| `forgery_detection.py` | 100.00 % |
| `rolling_stock.py` | 100.00 % |
| `source_locator.py` | 98.58 % |
| `cover_logistics.py` | 96.96 % |

The two modules below 100 % are tracked in
[`../../TODO.md`](../../TODO.md) (Round-2 section): their uncovered lines are
defensive guards that are unreachable on valid inputs by construction
(Bellman–Ford parent-chain guards, the zero-bottleneck return, the
route-decomposition break) plus the Gauss–Newton "no improvement after
halving" stop, a safety net that the well-conditioned inverse-square forward
model does not trigger. Every branch that *can* run when something goes wrong
— the reverse-arc cancellation path, the recursive matching reassignment, the
Gauss–Newton line-search halving and iteration-budget exhaustion — is now
exercised by a real regression test.

Regenerate with:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```
