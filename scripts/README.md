# scripts — Octopussy: FABERGÉ

Thin orchestrators, one per mission phase. Business logic lives in
`src/octopussy/`. Each script bootstraps `src/` onto `sys.path`, so plain
`python scripts/<name>.py` works from the package root.

| Script | Purpose |
|---|---|
| `mission_brief.py` | Print the frozen mission brief. |
| `mission_recon.py` | Run reconnaissance and print findings. |
| `mission_plan.py` | Print the ordered plan steps. |
| `mission_execute.py` | Run the pipelines; write `output/data/mission_outcome.json` + figures. |
| `mission_debrief.py` | Run and print the debrief lessons. |
| `demo_mission.py` | Full lifecycle via `run_mission`. |
| `z_generate_manuscript_variables.py` | Hydrate `{{TOKEN}}`s; render manuscript + figures. |

Run them with the package venv python (`uv run python scripts/x.py`) so the
`bond-api` path dependency resolves.
