"""Brief the FABERGÉ mission: print the frozen mission definition."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa: E402

from octopussy.mission import MissionProvider  # noqa: E402  (imported with sys.path bootstrapped above)


def main() -> int:
    brief = MissionProvider().brief()
    print(f"{brief.codename} — Octopussy special-agent mission")
    print(f"film: {brief.film}")
    print("objectives:")
    for objective in brief.objectives:
        print(f"  - {objective}")
    print("assets:")
    for asset in brief.assets:
        print(f"  - {asset.kind}: {asset.name} {asset.payload}")
    print("constraints:")
    for constraint in brief.constraints:
        print(f"  - {constraint.kind}: {constraint.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
