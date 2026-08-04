"""Run reconnaissance for the FABERGÉ mission and print the findings."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa: E402

from bond_api.protocol import ReconRequest  # noqa: E402
from octopussy.mission import MissionProvider  # noqa: E402


def main() -> int:
    goal = sys.argv[1] if len(sys.argv) > 1 else "survey the FABERGÉ target"
    report = MissionProvider().recon(ReconRequest(goal))
    print(f"recon goal: {report.findings[0].detail if report.findings else goal}")
    for finding in report.findings:
        print(f"  * {finding.label}: {finding.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
