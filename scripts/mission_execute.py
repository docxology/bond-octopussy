"""Execute the FABERGÉ mission: run the pipelines and persist artifacts.

Writes ``output/data/mission_outcome.json`` (deterministic, no wall clock) and
renders the FABERGÉ figures under ``output/figures/``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa: E402

from octopussy.figures import generate_all  # noqa: E402
from octopussy.mission import MissionProvider  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    provider = MissionProvider()
    brief = provider.brief()
    plan = provider.plan(brief)
    outcome = provider.execute(plan)
    payload = {
        "success": outcome.success,
        "results": outcome.results,
        "provenance": {
            "package_version": outcome.provenance.package_version,
            "seed": outcome.provenance.seed,
            "input_hash": outcome.provenance.input_hash,
        },
    }
    data_dir = PROJECT_ROOT / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "mission_outcome.json").write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str), encoding="utf-8"
    )
    figures = generate_all(PROJECT_ROOT / "output" / "figures")
    print(f"success: {outcome.success}")
    print(f"forgery worst: {outcome.results['forgery']['worst']}")
    print(f"concealment flagged: {outcome.results['concealment']['flagged']}")
    print(f"figures written: {len(figures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
