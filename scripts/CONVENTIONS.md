# Script conventions — octopussy

- One thin CLI per mission phase; each is a `main() -> int` returning 0 on
  success and using `raise SystemExit(main())`.
- `sys.path` bootstrap with `# noqa: E402` on the import lines that follow.
- Prefer `PROJECT_ROOT` derived from `Path(__file__).resolve().parents[1]` for
  stable artifact paths.
- Never hardcode numbers that flow through `manuscript_variables.py`.
- Keep output deterministic (fixed seed; no wall-clock in persisted files).
