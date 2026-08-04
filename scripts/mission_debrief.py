"""Debrief the FABERGÉ mission: run it and print the lessons learned."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa: E402

from bond_api.protocol import run_mission, ReconRequest  # noqa: E402
from octopussy.mission import MissionProvider  # noqa: E402


def main() -> int:
    debrief = run_mission(MissionProvider(), ReconRequest("debrief the FABERGÉ mission"))
    print(f"mission success: {debrief.outcome.success}")
    print("lessons learned:")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
