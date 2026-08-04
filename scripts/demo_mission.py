"""Run the full FABERGÉ mission lifecycle through the frozen BOND-API flow."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa: E402

from bond_api.protocol import run_mission, ReconRequest  # noqa: E402
from octopussy.mission import CODENAME, MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    print(f"{provider.brief().codename} — full mission lifecycle")
    debrief = run_mission(provider, ReconRequest(f"run the {CODENAME} mission"))
    outcome = debrief.outcome
    print(f"success: {outcome.success}")
    print(f"provenance: seed={outcome.provenance.seed} input_hash={outcome.provenance.input_hash[:12]}...")
    print("results:")
    for key, value in outcome.results.items():
        print(f"  - {key}: {value}")
    print("debrief lessons:")
    for lesson in debrief.lessons:
        print(f"  * {lesson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
