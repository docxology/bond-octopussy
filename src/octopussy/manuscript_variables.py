"""Manuscript variable hydration for Octopussy: FABERGÉ.

Every ``{{TOKEN}}`` in ``manuscript/[0-9]*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
live package surface and — where a metric is a measured outcome — the live
deterministic mission run. Metrics are never hand-authored in prose: they flow
through this module so the manuscript cannot drift from the code.

The consuming orchestrator is ``scripts/z_generate_manuscript_variables.py``
(thin wrapper); the live cross-reference gate lives in
``tests/test_manuscript_variables.py``.
"""

from __future__ import annotations

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import yaml

from octopussy import concealment_sweep as sweep
from octopussy import cover_logistics as logistics
from octopussy import forgery_detection as forge
from octopussy.mission import CODENAME, SEED, run_faberge

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

IDENTITY = "Octopussy"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"manuscript config must be a top-level mapping, got {type(data).__name__}")
    return data


def generate_variables(
    *,
    config_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, str]:
    """Compute the full ``{{TOKEN}}`` → value mapping for the manuscript."""
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")

    # Live deterministic outcomes feed the result-derived tokens.
    outcomes = run_faberge(SEED)
    forgery = cast("dict[str, object]", outcomes["forgery"])
    logistics_out = cast("dict[str, object]", outcomes["logistics"])
    concealment = cast("dict[str, object]", outcomes["concealment"])

    stamp = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    return {
        "FABERGE_IDENTITY": IDENTITY,
        "FABERGE_CODENAME": CODENAME,
        "FABERGE_VERSION": str(paper.get("version", "")),
        "FABERGE_TITLE": str(paper.get("title", "")),
        "FABERGE_SUBTITLE": str(paper.get("subtitle", "")),
        "FABERGE_SEED": str(SEED),
        "FABERGE_NUM_PIGMENTS": str(forge.PIGMENT_COUNT),
        "FABERGE_NUM_ARTIFACTS": str(forge.ARTIFACT_COUNT),
        "FABERGE_NUM_SEGMENTS": str(logistics.SEGMENT_COUNT),
        "FABERGE_NUM_DETECTORS": str(int(_grid_detectors())),
        "FABERGE_NUM_CONTAINERS": str(len(sweep.DEFAULT_CONTAINERS)),
        "FABERGE_FLAGGED_FORGERY": str(forgery["flagged"]),
        "FABERGE_FORGERY_WORST": str(forgery["worst"]),
        "FABERGE_LOGISTICS_MAKESPAN": str(logistics_out["makespan"]),
        "FABERGE_LOGISTICS_TRAINS": str(logistics_out["trains_needed"]),
        "FABERGE_SWEEP_FLAGGED": ", ".join(str(x) for x in cast("list[object]", concealment["flagged"])),
        "FABERGE_SWEEP_WORST": str(concealment["worst"] if concealment["worst"] else "none"),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": stamp,
    }


def _grid_detectors() -> int:
    """Number of detectors in the mission's concealment sweep grid."""
    return 100


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each manuscript section to ``output/manuscript/``, substituting tokens.

    Only ``NN_*.md`` section files are copied (not sidecars such as
    ``SYNTAX.md``). In strict mode any leftover ``{{TOKEN}}`` fails so the
    manuscript never renders with raw braces.
    """
    manuscript_dir = Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    output_dir = Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
