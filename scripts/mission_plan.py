"""Plan the FABERGÉ mission: print the ordered plan steps."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa: E402

from octopussy.mission import MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    for i, step in enumerate(plan.steps, start=1):
        print(f"{i}. {step.name} — {step.action} {step.params}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
