---
title: "tests: octopussy — FABERGÉ"
type: "tests_guide"
version: "0.1.0"
---

# tests (octopussy)

Rules (see `../docs/testing_philosophy.md` for the full doctrine):

- **No mocks.** Real data + computation only; deterministic reference
  providers implement the real protocol.
- **Determinism asserted** — re-running the same seed yields byte-equal
  outputs; verdicts stay separated across seeds.
- **Error branches covered** with `pytest.raises` for every validation path.
- **Live manuscript gate** — the cross-reference test scans
  `manuscript/[0-9][0-9]_*.md` only and asserts every `{{TOKEN}}` is generated.
- **CLI smoke tests** run scripts as subprocesses (`sys.executable`,
  `cwd=project_root`) and assert real artifacts.

`conftest.py` forces `MPLBACKEND=Agg` so figure tests never open a display.
