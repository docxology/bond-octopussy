"""Hydrate manuscript tokens and render the FABERGÉ figures.

Writes ``output/data/manuscript_variables.json`` and the resolved manuscript
tree under ``output/manuscript/``, then renders all FABERGÉ figures. Runs in
strict mode: any unresolved ``{{TOKEN}}`` in a numbered section fails it.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))  # noqa: E402

from octopussy.figures import generate_all  # noqa: E402
from octopussy.manuscript_variables import generate_variables, resolve_manuscript_tree  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    variables = generate_variables()
    data_dir = PROJECT_ROOT / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "manuscript_variables.json").write_text(
        json.dumps(variables, sort_keys=True, indent=2), encoding="utf-8"
    )
    output_dir, resolved = resolve_manuscript_tree(variables)
    figures = generate_all(PROJECT_ROOT / "output" / "figures")
    print(f"resolved {len(resolved)} manuscript sections to {output_dir}")
    print(f"rendered {len(figures)} figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
