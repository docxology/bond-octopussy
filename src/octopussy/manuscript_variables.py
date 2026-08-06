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
from pathlib import Path
from typing import Any, cast

import yaml

from octopussy import concealment_sweep as sweep
from octopussy import cover_logistics as logistics
from octopussy import forgery_detection as forge
from octopussy.mission import CODENAME, PIPELINE_COUNT, SEED, SWEEP_DETECTORS, SWEEP_GRID, run_faberge

__all__ = [
    "borderline_anachronism",
    "generate_variables",
    "load_manuscript_config",
    "resolve_manuscript_tree",
]

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


def borderline_anachronism(
    exhibit: tuple[forge.Artifact, ...] | None = None,
    library: dict[str, forge.Pigment] | None = None,
) -> tuple[str, int, int, float]:
    """Identify the exhibit's *hardest* forgery: the least-modern fake.

    A fake built entirely from modern material is trivially caught — any
    channel would flag it. The discriminating case is the one with the least
    modern material in it, so the selection criterion is the **smallest
    anachronistic weight fraction** among artifacts that have any anachronism
    at all; ties break toward the smaller introduction gap.

    "Least modern" is relative to *this* exhibit and is not a claim that the
    selected artifact is mostly period-correct: the returned fraction is the
    measurement, and on the shipped exhibit it is half the mixture by weight.
    The results section quotes the fraction rather than characterizing it, so
    that a change to the exhibit cannot leave a stale adjective behind.

    Returns ``(artifact_name, claimed_year, min_gap_years,
    anachronistic_weight_fraction)`` where ``min_gap_years`` is how far the
    earliest offending pigment post-dates the claimed year, and the fraction is
    of the mixture's total weight. The results section quotes these from the
    exhibit rather than from memory.

    Raises :class:`ValueError` when the exhibit contains no anachronism at all
    — a silent "no borderline case" would let the results prose describe an
    artifact that is not there.
    """
    artifacts = forge.DEFAULT_EXHIBIT if exhibit is None else exhibit
    pigments = forge.PIGMENT_LIBRARY if library is None else library
    best: tuple[str, int, int, float] | None = None
    for artifact in artifacts:
        total = sum(weight for _, weight in artifact.mixture)
        if total <= 0.0:
            continue
        modern = 0.0
        min_gap: int | None = None
        for name, weight in artifact.mixture:
            gap = pigments[name].introduced - artifact.claimed_year
            if gap <= 0:
                continue
            modern += weight
            min_gap = gap if min_gap is None else min(min_gap, gap)
        if min_gap is None:
            continue
        candidate = (artifact.name, artifact.claimed_year, min_gap, modern / total)
        if best is None or (candidate[3], candidate[2]) < (best[3], best[2]):
            best = candidate
    if best is None:
        raise ValueError("exhibit contains no anachronistic pigment; the borderline case token has no referent")
    return best


def generate_variables(*, config_path: str | Path | None = None) -> dict[str, str]:
    """Compute the full ``{{TOKEN}}`` → value mapping for the manuscript.

    No wall-clock value is emitted. A generation timestamp used to be part of
    this mapping and was written into ``output/data/manuscript_variables.json``
    and into the rendered experimental-setup section, which made the package's
    own "regenerating leaves a byte-identical tree" claim false: two runs a
    second apart differed. Determinism is worth more here than knowing when the
    artifacts were last built, and mission provenance already carries an
    ``input_hash``. ``PYTHON_VERSION`` is the one remaining environment-derived
    value, so byte-identity holds for a fixed interpreter version — see
    ``tests/test_manuscript_variables.py::test_regeneration_is_byte_identical``.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")

    # Live deterministic outcomes feed the result-derived tokens.
    outcomes = run_faberge(SEED)
    forgery = cast("dict[str, object]", outcomes["forgery"])
    logistics_out = cast("dict[str, object]", outcomes["logistics"])
    concealment = cast("dict[str, object]", outcomes["concealment"])
    varnish_out = cast("dict[str, object]", outcomes["varnish"])
    rolling_out = cast("dict[str, object]", outcomes["rolling_stock"])
    source_out = cast("dict[str, object]", outcomes["source_locator"])

    borderline_name, borderline_year, borderline_gap, borderline_modern = borderline_anachronism()

    # Per-artifact forgery verdict tokens (the results table). Positional so a
    # rename of an exhibit artifact updates the table without a prose edit.
    verdicts = cast("list[dict[str, object]]", forgery["verdicts"])
    verdict_tokens: dict[str, str] = {}
    for index, verdict in enumerate(verdicts, start=1):
        prefix = f"FABERGE_VERDICT_{index}"
        verdict_tokens[f"{prefix}_ARTIFACT"] = str(verdict["artifact"])
        verdict_tokens[f"{prefix}_LEVEL"] = str(verdict["level"])
        verdict_tokens[f"{prefix}_SCORE"] = f"{float(cast('float', verdict['score'])):.2f}"
        detected = cast("list[str]", verdict["anachronistic"])
        verdict_tokens[f"{prefix}_ANACH"] = ", ".join(detected) if detected else "none"

    return {
        "FABERGE_IDENTITY": IDENTITY,
        "FABERGE_CODENAME": CODENAME,
        "FABERGE_VERSION": str(paper.get("version", "")),
        "FABERGE_TITLE": str(paper.get("title", "")),
        "FABERGE_SUBTITLE": str(paper.get("subtitle", "")),
        "FABERGE_SEED": str(SEED),
        "FABERGE_NUM_PIPELINES": str(PIPELINE_COUNT),
        "FABERGE_NUM_PIGMENTS": str(forge.PIGMENT_COUNT),
        "FABERGE_NUM_ARTIFACTS": str(forge.ARTIFACT_COUNT),
        "FABERGE_NUM_BANDS": str(forge.BAND_COUNT),
        "FABERGE_BAND_MIN_NM": f"{forge.BAND_MIN_NM:.0f}",
        "FABERGE_BAND_MAX_NM": f"{forge.BAND_MAX_NM:.0f}",
        "FABERGE_NUM_SEGMENTS": str(logistics.SEGMENT_COUNT),
        "FABERGE_NUM_STATIONS": str(len(logistics.RailNetwork().nodes)),
        "FABERGE_NUM_DETECTORS": str(SWEEP_DETECTORS),
        "FABERGE_GRID_NX": str(SWEEP_GRID.nx),
        "FABERGE_GRID_NY": str(SWEEP_GRID.ny),
        "FABERGE_NUM_CONTAINERS": str(len(sweep.DEFAULT_CONTAINERS)),
        "FABERGE_NUM_CATEGORIES": str(sweep.CATALOG_SIZE),
        "FABERGE_SCREENED_ARTIFACTS": str(forgery["screened"]),
        "FABERGE_FLAGGED_FORGERY": str(forgery["flagged"]),
        "FABERGE_FORGERY_WORST": str(forgery["worst"]),
        "FABERGE_BORDERLINE_ARTIFACT": borderline_name,
        "FABERGE_BORDERLINE_YEAR": str(borderline_year),
        "FABERGE_BORDERLINE_GAP_YEARS": str(borderline_gap),
        "FABERGE_BORDERLINE_MODERN_PCT": f"{100.0 * borderline_modern:.0f}",
        "FABERGE_LOGISTICS_UNITS": str(logistics_out["payload_units"]),
        "FABERGE_LOGISTICS_COST": str(logistics_out["total_cost"]),
        "FABERGE_LOGISTICS_MAKESPAN": str(logistics_out["makespan"]),
        "FABERGE_LOGISTICS_DEADLINE": str(logistics_out["deadline"]),
        "FABERGE_LOGISTICS_SLACK": str(logistics_out["slack"]),
        "FABERGE_LOGISTICS_TRAINS": str(logistics_out["trains_needed"]),
        "FABERGE_SWEEP_FLAGGED": ", ".join(str(x) for x in cast("list[object]", concealment["flagged"])),
        "FABERGE_SWEEP_WORST": str(concealment["worst"] if concealment["worst"] else "none"),
        # Varnish ageing (forgery depth). Both surfaces are exhibit artifacts;
        # the *_TRUE_AGE tokens are the authored ground truth the estimator is
        # scored against, and the scatter tokens are its measured error bar.
        "FABERGE_VARNISH_GENUINE_ARTIFACT": str(varnish_out["genuine_artifact"]),
        "FABERGE_VARNISH_FAKE_ARTIFACT": str(varnish_out["fake_artifact"]),
        "FABERGE_VARNISH_TRUE_AGE": f"{float(cast('float', varnish_out['genuine_true_age'])):.0f}",
        "FABERGE_VARNISH_FAKE_TRUE_AGE": f"{float(cast('float', varnish_out['fake_true_age'])):.0f}",
        "FABERGE_VARNISH_TRIALS": str(varnish_out["trials"]),
        "FABERGE_VARNISH_TOLERANCE": f"{float(cast('float', varnish_out['tolerance_years'])):.0f}",
        "FABERGE_VARNISH_GENUINE_AGE": str(varnish_out["genuine_estimated_age"]),
        "FABERGE_VARNISH_GENUINE_VERDICT": str(varnish_out["genuine_verdict"]),
        "FABERGE_VARNISH_GENUINE_STD": str(varnish_out["genuine_age_std"]),
        "FABERGE_VARNISH_GENUINE_MIN": str(varnish_out["genuine_age_min"]),
        "FABERGE_VARNISH_GENUINE_MAX": str(varnish_out["genuine_age_max"]),
        "FABERGE_VARNISH_GENUINE_CONSISTENT_TRIALS": str(varnish_out["genuine_consistent_trials"]),
        "FABERGE_VARNISH_GENUINE_VERDICT_SPREAD": str(varnish_out["genuine_verdict_spread"]),
        "FABERGE_VARNISH_GENUINE_VERDICTS_SEEN": str(varnish_out["genuine_verdicts_seen"]),
        "FABERGE_VARNISH_FAKE_AGE": str(varnish_out["fake_estimated_age"]),
        "FABERGE_VARNISH_FAKE_VERDICT": str(varnish_out["fake_verdict"]),
        "FABERGE_VARNISH_FAKE_CLOSENESS": str(varnish_out["fake_closeness"]),
        "FABERGE_VARNISH_FAKE_STD": str(varnish_out["fake_age_std"]),
        "FABERGE_VARNISH_FAKE_REJECTED_TRIALS": str(varnish_out["fake_rejected_trials"]),
        "FABERGE_VARNISH_CLAIMED": str(varnish_out["claimed_year"]),
        # Rolling stock (logistics depth) + the cross-pipeline cover check.
        "FABERGE_ROLLING_TRIPS": str(rolling_out["trips"]),
        "FABERGE_ROLLING_MATCHING": str(rolling_out["matching_edges"]),
        "FABERGE_ROLLING_TRAINSETS": str(rolling_out["trainsets"]),
        "FABERGE_ROLLING_DEADHEAD": str(rolling_out["deadhead_minutes"]),
        "FABERGE_ROLLING_DEPOT_COST": str(rolling_out["depot_assignment_cost"]),
        "FABERGE_COVER_ROUTED_LEGS": str(rolling_out["routed_legs"]),
        "FABERGE_COVER_CORRIDOR_COVERED": str(rolling_out["corridor_covered"]),
        "FABERGE_COVER_FLEET_SUFFICIENT": str(rolling_out["fleet_sufficient"]),
        # Source localization (sweep depth).
        "FABERGE_SOURCE_ERROR_M": str(source_out["error_m"]),
        "FABERGE_SOURCE_STD_M": str(source_out["position_std_m"]),
        "FABERGE_SOURCE_INTENSITY": str(source_out["intensity"]),
        "FABERGE_SOURCE_TRUE_INTENSITY": f"{float(cast('float', source_out['true_intensity'])):.0f}",
        "FABERGE_SOURCE_RESIDUAL": str(source_out["residual"]),
        "FABERGE_SOURCE_ITERATIONS": str(source_out["iterations"]),
        "FABERGE_SOURCE_CONVERGED": str(source_out["converged"]),
        "PYTHON_VERSION": platform.python_version(),
        **verdict_tokens,
    }


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
