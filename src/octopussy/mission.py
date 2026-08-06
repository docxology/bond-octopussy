"""FABERGÉ — the Octopussy mission adapter for the frozen BOND-API protocol.

:mod:`octopussy.mission` is the thin boundary between the six pure domain
modules — :mod:`octopussy.forgery_detection`, :mod:`octopussy.cover_logistics`,
:mod:`octopussy.concealment_sweep`, :mod:`octopussy.varnish_ageing`,
:mod:`octopussy.rolling_stock`, and :mod:`octopussy.source_locator` — and the
BOND-API ``MissionProvider`` contract (see ``bond_api.protocol``). It is the
only module in this package that imports ``bond_api``; the domain core stays
importable on its own.

The orchestrator discovers this film by slug: importing ``octopussy.mission``
exposes the :class:`MissionProvider` class (discovery contract). Executing the
mission runs the six investigative pipelines end-to-end, deterministically,
under a fixed seed, and returns their verdicts plus full provenance.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

from octopussy import concealment_sweep as sweep
from octopussy import cover_logistics as logistics
from octopussy import forgery_detection as forge
from octopussy import rolling_stock as rolling
from octopussy import source_locator as locator
from octopussy import varnish_ageing as varnish

__all__ = [
    "CODENAME",
    "FILM",
    "PIPELINES",
    "PIPELINE_COUNT",
    "SEED",
    "SWEEP_DETECTORS",
    "SWEEP_GRID",
    "MissionProvider",
    "gadget_registry",
    "register_gadgets",
    "run_faberge",
]

#: Manuscript identity of this film package.
FILM = "octopussy"
CODENAME = "FABERGÉ"
PACKAGE_VERSION = "0.1.0"
#: Fixed deterministic seed for every pipeline in this package.
SEED = 7

#: The investigative pipelines :func:`run_faberge` drives, in execution order.
#: This tuple *is* the contract its result keys are checked against, so the
#: count in prose can never drift from the count in code.
PIPELINES: tuple[str, ...] = (
    "forgery",
    "logistics",
    "concealment",
    "varnish",
    "rolling_stock",
    "source_locator",
)
PIPELINE_COUNT: int = len(PIPELINES)

#: Scenario parameters for the execute stage (deterministic scenario).
_FORGERY_NOISE = 0.02
_LOGISTICS_SOURCE = "dover"
_LOGISTICS_SINK = "monastery"
_LOGISTICS_UNITS = 3
_LOGISTICS_DEADLINE = 400
_LOGISTICS_CAPACITY = 2
#: The mission's detector lattice. Public because manuscript variables and the
#: brief derive their detector counts from it rather than restating a literal.
SWEEP_GRID = sweep.SweepGrid((0.0, 0.0), 2.0, 10, 10)
#: Number of detectors in :data:`SWEEP_GRID`, derived — never hand-written.
SWEEP_DETECTORS = int(SWEEP_GRID.nx * SWEEP_GRID.ny)
_SWEEP_BACKGROUND = 40.0
_SWEEP_SOURCE = sweep.RadiationSource((7.0, 7.0), 800.0)
_SWEEP_THRESHOLD = 3.0

# Varnish-ageing scenario. The two surfaces are *exhibit artifacts*, named
# here and looked up in `forge.DEFAULT_EXHIBIT`: the varnish channel reads the
# same objects the pigment screen reads, and each surface's claimed year comes
# from its exhibit record rather than from a constant in this file.
_VARNISH_GENUINE_ARTIFACT = "tsar_egg"  # natural shellac varnish, era-consistent mixture
_VARNISH_FAKE_ARTIFACT = "forged_dupe"  # modern acrylic varnish over modern pigments
_VARNISH_CURRENT = 2026
#: Authored scenario ground truth: how long ago the forger's coat was applied.
#: The genuine surface's true age is *not* a constant — it is derived from that
#: artifact's claimed year, which is the null hypothesis the channel tests.
_VARNISH_REVARNISH_AGE = 3.0
_VARNISH_NOISE = 0.02
#: Noise realizations used to measure the dating estimator's own error bar.
_VARNISH_TRIALS = 32

# Rolling-stock scenario: one long corridor chain plus a parallel spur service.
_ROLLING_TURNAROUND = 20
_ROLLING_TRIPS: tuple[rolling.Trip, ...] = (
    rolling.Trip("T1", "dover", "calais", 60, 100),
    rolling.Trip("T2", "calais", "amien", 120, 175),
    rolling.Trip("T3", "amien", "paris", 195, 265),
    rolling.Trip("T4", "paris", "garrison", 285, 335),
    rolling.Trip("T5", "garrison", "monastery", 355, 400),
    rolling.Trip("T6", "dover", "calais", 90, 130),
    rolling.Trip("T7", "calais", "amien", 150, 205),
)

# Depot-assignment cost matrix (trainsets x routes, deadhead minutes).
_DEPOT_COST: tuple[tuple[float, ...], ...] = (
    (10.0, 25.0, 15.0),
    (20.0, 12.0, 30.0),
    (18.0, 22.0, 16.0),
)


def _varnish_rng(seed: int) -> np.random.Generator:
    """The varnish channel's own generator, derived from its pipeline index.

    Separate from the forgery channel's stream so that changing one pipeline's
    draw count cannot silently move another pipeline's numbers. Tests replicate
    this derivation to bind reported ages to the exhibit they came from.
    """
    return np.random.default_rng((seed, PIPELINES.index("varnish")))


def _exhibit_artifact(name: str) -> forge.Artifact:
    """Look one artifact up in the live exhibit, failing loudly if it is gone."""
    for artifact in forge.DEFAULT_EXHIBIT:
        if artifact.name == name:
            return artifact
    raise KeyError(f"{name!r} is not in forge.DEFAULT_EXHIBIT; the varnish scenario has no surface to date")


def _unvarnished_reference(artifact: forge.Artifact) -> np.ndarray:
    """Reflectance of an exhibit artifact's substrate with the varnish removed.

    The examiner's reference sample: the same pigment mixture as the object,
    minus the varnish layer (an unvarnished edge or a cross-section). Reading
    it off the exhibit record is what couples the varnish channel to the same
    objects the pigment screen sees.
    """
    substrate = tuple((name, w) for name, w in artifact.mixture if forge.PIGMENT_LIBRARY[name].category != "varnish")
    if not substrate:
        raise ValueError(f"{artifact.name!r} is varnish only; it has no substrate to reference")
    return forge.mix_spectrum(substrate)


def _input_hash(codename: str, objectives: tuple[str, ...], plan: MissionPlan) -> str:
    """Deterministic sha256 fingerprint of the mission's defining inputs."""
    payload = {
        "codename": codename,
        "objectives": list(objectives),
        "steps": [{"name": step.name, "action": step.action, "params": step.params} for step in plan.steps],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_faberge(seed: int = SEED, *, trips: tuple[rolling.Trip, ...] = _ROLLING_TRIPS) -> dict[str, object]:
    """Run all six investigative pipelines; return structured results.

    The returned mapping has exactly :data:`PIPELINE_COUNT` top-level keys —
    ``forgery``, ``logistics``, ``concealment``, ``varnish``,
    ``rolling_stock``, ``source_locator`` — one per pipeline. Deterministic
    under the fixed ``seed``: every verdict, route, hotspot, age estimate,
    trainset chain and source fix is computed (never faked), and the result is
    JSON-serializable for mission reports.

    ``trips`` is the circus schedule the rolling-stock pipeline circulates and
    the cross-pipeline cover check is measured against. It is injectable so
    that the negative control for that check — a schedule that does *not* cover
    the routed corridor — exercises this function rather than a re-implemented
    copy of it; the mission always runs the default.
    """
    # 1) Forgery detection — spectral/UV screen of the exhibit.
    rng = np.random.default_rng(seed)
    verdicts = forge.screen_collection(forge.DEFAULT_EXHIBIT, rng=rng, noise_std=_FORGERY_NOISE)
    forgery = {
        "screened": len(verdicts),
        "flagged": sum(1 for v in verdicts if v.level in (forge.ForgeryLevel.LIKELY_FORGED, forge.ForgeryLevel.FORGED)),
        "worst": max(verdicts, key=lambda v: v.score).artifact,
        "verdicts": [
            {
                "artifact": v.artifact,
                "level": v.level.value,
                "score": round(float(v.score), 4),
                "reasons": list(v.reasons),
                "anachronistic": list(v.anachronistic),
            }
            for v in verdicts
        ],
    }

    # 2) Cover logistics — min-cost flow of the payload under the circus cover.
    network = logistics.RailNetwork()
    transfer = logistics.plan_transfer(
        network,
        _LOGISTICS_SOURCE,
        _LOGISTICS_SINK,
        _LOGISTICS_UNITS,
        deadline=_LOGISTICS_DEADLINE,
        train_capacity=_LOGISTICS_CAPACITY,
    )
    logistics_results = {
        "source": transfer.source,
        "sink": transfer.sink,
        "payload_units": transfer.payload_units,
        "feasible": transfer.feasible,
        "total_cost": transfer.total_cost,
        "makespan": transfer.makespan,
        "deadline": transfer.deadline,
        "slack": transfer.slack,
        "trains_needed": transfer.trains_needed,
        "train_capacity": transfer.train_capacity,
        "edges_used": [list(e) for e in transfer.edges_used],
    }

    # 3) Concealment sweep — radiation + shape/mass anomaly fusion.
    positions, counts = sweep.simulate_sweep(SWEEP_GRID, _SWEEP_BACKGROUND, (_SWEEP_SOURCE,), seed=seed)
    background = sweep.estimate_background(counts)
    anomaly = sweep.anomaly_map(counts, background)
    hits = sweep.detect_hotspots(counts, anomaly, _SWEEP_THRESHOLD)
    report = sweep.fuse_concealment_report(hits, sweep.DEFAULT_CONTAINERS)
    concealment = {
        "grid_size": SWEEP_DETECTORS,
        "hotspots": [{"position": list(h.position), "score": round(float(h.score), 3)} for h in hits],
        "suspicious": [
            {"kind": e.kind, "name": e.name, "score": round(float(e.score), 3), "detail": e.detail}
            for e in report.entries
        ],
        "flagged": list(report.flagged),
        "worst": report.worst.name if report.worst else None,
    }

    # 4) Varnish ageing — date two *exhibit* surfaces against their claimed era.
    #    Both surfaces are artifacts from forge.DEFAULT_EXHIBIT: the varnish
    #    channel reads the same objects the pigment screen reads, through a
    #    different physical observable (film chemistry, not composition).
    #    Alongside each single dating we measure the estimator's own error bar
    #    by re-observing the surface under independent noise draws — without it
    #    a single verdict is an unfalsifiable claim.
    varnish_rng = _varnish_rng(seed)
    genuine_art = _exhibit_artifact(_VARNISH_GENUINE_ARTIFACT)
    fake_art = _exhibit_artifact(_VARNISH_FAKE_ARTIFACT)
    genuine_ref = _unvarnished_reference(genuine_art)
    fake_ref = _unvarnished_reference(fake_art)
    genuine_true_age = float(_VARNISH_CURRENT - genuine_art.claimed_year)
    fake_true_age = float(_VARNISH_REVARNISH_AGE)

    genuine_measured = varnish.measure_varnished_surface(
        genuine_ref, genuine_true_age, rng=varnish_rng, noise_std=_VARNISH_NOISE
    )
    fake_measured = varnish.measure_varnished_surface(
        fake_ref, fake_true_age, rng=varnish_rng, noise_std=_VARNISH_NOISE
    )
    genuine_assess = varnish.date_varnished_surface(
        genuine_measured, genuine_ref, genuine_art.claimed_year, _VARNISH_CURRENT
    )
    fake_assess = varnish.date_varnished_surface(fake_measured, fake_ref, fake_art.claimed_year, _VARNISH_CURRENT)
    genuine_scatter = varnish.age_recovery_scatter(
        genuine_ref, genuine_true_age, rng=varnish_rng, trials=_VARNISH_TRIALS, noise_std=_VARNISH_NOISE
    )
    fake_scatter = varnish.age_recovery_scatter(
        fake_ref, fake_true_age, rng=varnish_rng, trials=_VARNISH_TRIALS, noise_std=_VARNISH_NOISE
    )
    genuine_verdicts = [
        varnish.age_verdict(genuine_art.claimed_year, _VARNISH_CURRENT, age)[0] for age in genuine_scatter.ages
    ]
    genuine_consistent = sum(1 for v in genuine_verdicts if v is varnish.AgeVerdict.CONSISTENT)
    genuine_spread = ", ".join(
        f"{level.value}×{genuine_verdicts.count(level)}"
        for level in varnish.AgeVerdict
        if genuine_verdicts.count(level)
    )
    fake_rejected = sum(
        1
        for age in fake_scatter.ages
        if varnish.age_verdict(fake_art.claimed_year, _VARNISH_CURRENT, age)[0] is varnish.AgeVerdict.TOO_YOUNG
    )
    varnish_block = {
        "genuine_artifact": genuine_art.name,
        "fake_artifact": fake_art.name,
        "claimed_year": genuine_art.claimed_year,
        "current_year": _VARNISH_CURRENT,
        "trials": _VARNISH_TRIALS,
        "tolerance_years": genuine_scatter.tolerance_years,
        "genuine_true_age": genuine_true_age,
        "genuine_estimated_age": round(float(genuine_assess.estimated_age), 1),
        "genuine_verdict": genuine_assess.verdict.value,
        "genuine_age_std": round(float(genuine_scatter.std_age), 1),
        "genuine_age_min": round(float(genuine_scatter.min_age), 1),
        "genuine_age_max": round(float(genuine_scatter.max_age), 1),
        "genuine_consistent_trials": genuine_consistent,
        "genuine_verdict_spread": genuine_spread,
        "genuine_verdicts_seen": len({v.value for v in genuine_verdicts}),
        "fake_true_age": fake_true_age,
        "fake_estimated_age": round(float(fake_assess.estimated_age), 1),
        "fake_verdict": fake_assess.verdict.value,
        "fake_closeness": round(float(fake_assess.closeness), 3),
        "fake_age_std": round(float(fake_scatter.std_age), 1),
        "fake_rejected_trials": fake_rejected,
    }

    # 5) Rolling-stock circulation — how many circus trainsets cover the trips,
    #    and whether that fleet can actually carry the routed corridor plan.
    #    The two pipelines are only linked if something compares them, so the
    #    comparison is computed here and reported: every segment the flow routes
    #    must appear as a scheduled circus trip, and the trains the flow needs
    #    must not exceed the trainsets the schedule fields.
    fleet = rolling.fleet_circulation(trips, _ROLLING_TURNAROUND)
    depot = rolling.kuhn_munkres([list(row) for row in _DEPOT_COST])
    scheduled_legs = {(trip.origin, trip.destination) for trip in trips}
    routed_legs = {(origin, destination) for origin, destination, _ in transfer.edges_used}
    uncovered = sorted(routed_legs - scheduled_legs)
    rolling_block = {
        "trips": fleet.trips,
        "trainsets": fleet.trainsets,
        "matching_edges": fleet.matching_edges,
        "deadhead_minutes": fleet.deadhead_minutes,
        "turnaround": fleet.turnaround,
        "chains": [list(chain) for chain in fleet.chains],
        "depot_assignment": [[int(r), int(c), round(float(cost), 1)] for r, c, cost in depot],
        "depot_assignment_cost": float(sum(cost for _, _, cost in depot)),
        # Cross-pipeline cover check (logistics x rolling stock).
        "routed_legs": len(routed_legs),
        "uncovered_legs": [list(leg) for leg in uncovered],
        "corridor_covered": not uncovered,
        "trains_needed": transfer.trains_needed,
        "fleet_sufficient": bool(transfer.trains_needed <= fleet.trainsets),
    }

    # 6) Source localization — locate the concealed emitter from the sweep,
    #    with the approximate positional uncertainty the fit implies.
    localized = locator.locate_from_sweep(SWEEP_GRID, counts, background)
    position_error = (
        (localized.position[0] - _SWEEP_SOURCE.position[0]) ** 2
        + (localized.position[1] - _SWEEP_SOURCE.position[1]) ** 2
    ) ** 0.5
    std_x, std_y, _ = locator.localization_uncertainty(
        SWEEP_GRID.detector_positions(),
        counts.ravel(),
        float(np.mean(background)),
        localized,
        SWEEP_GRID.standoff,
    )
    source_block = {
        "estimated_position": [round(float(p), 3) for p in localized.position],
        "true_position": list(_SWEEP_SOURCE.position),
        "true_intensity": float(_SWEEP_SOURCE.intensity),
        "error_m": round(float(position_error), 3),
        "position_std_m": round(float((std_x * std_x + std_y * std_y) ** 0.5), 3),
        "intensity": round(float(localized.intensity), 1),
        "residual": round(float(localized.residual_norm), 3),
        "converged": localized.converged,
        "iterations": localized.iterations,
    }

    results: dict[str, object] = {
        "forgery": forgery,
        "logistics": logistics_results,
        "concealment": concealment,
        "varnish": varnish_block,
        "rolling_stock": rolling_block,
        "source_locator": source_block,
    }
    if tuple(results) != PIPELINES:  # pragma: no cover — structural invariant
        raise AssertionError(f"run_faberge result keys {tuple(results)} drifted from PIPELINES {PIPELINES}")
    return results


class MissionProvider:  # noqa: N801 — class name is fixed by the discovery contract
    """FABERGÉ: detect forgeries, route the cargo, and sweep for the device."""

    film = FILM

    def brief(self) -> MissionBrief:
        """Declare the FABERGÉ mission: the three headline investigative objectives.

        Three objectives, six pipelines: each objective is served by a headline
        module plus a depth module (forgery + varnish ageing, logistics +
        rolling stock, sweep + source localization). The objective tuple is
        part of the mission fingerprint (:func:`_input_hash`), so it is kept
        stable across depth work.
        """
        return MissionBrief(
            film=self.film,
            codename=CODENAME,
            objectives=(
                "detect artifact forgeries via spectral/UV fingerprinting",
                "route smuggled payload under circus cover by min-cost flow",
                "sweep for a concealed nuclear device via radiation and mass anomaly",
            ),
            assets=(
                Asset(kind="scenario", name="exhibit", payload={"artifacts": forge.ARTIFACT_COUNT}),
                Asset(kind="scenario", name="corridor", payload={"segments": logistics.SEGMENT_COUNT}),
                Asset(kind="scenario", name="sweep", payload={"detectors": SWEEP_DETECTORS}),
            ),
            constraints=(
                Constraint(kind="determinism", detail="fixed seed, no random or wall-clock dependence"),
                Constraint(kind="cover", detail="cargo must ride the circus under capacity limits"),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, the available scenario assets, and the constraints."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="exhibit", detail=f"{forge.ARTIFACT_COUNT} artifacts screened by spectral/UV fingerprinting"
                ),
                Finding(label="corridor", detail=f"{logistics.SEGMENT_COUNT} rail segments form the circus corridor"),
                Finding(
                    label="sweep",
                    detail=f"{SWEEP_DETECTORS} detectors in the concealed-device sweep",
                ),
                Finding(label="constraints", detail="deterministic execution and cover-capacity limits apply"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the six pipeline steps plus a verification step."""
        return MissionPlan(
            steps=(
                Step(name="forge_screen", action="fingerprint_exhibit", params={"seed": SEED}),
                Step(name="route_cargo", action="min_cost_flow", params={"units": _LOGISTICS_UNITS}),
                Step(name="concealed_sweep", action="radiation_mass_fusion", params={"threshold": _SWEEP_THRESHOLD}),
                Step(
                    name="varnish_age",
                    action="yellowing_kinetics",
                    params={"surface": _VARNISH_GENUINE_ARTIFACT, "trials": _VARNISH_TRIALS},
                ),
                Step(name="rolling_stock", action="fleet_circulation", params={"turnaround": _ROLLING_TURNAROUND}),
                Step(name="source_locator", action="gauss_newton_localization", params={"tolerance": 1e-6}),
                Step(name="verify", action="collect_provenance", params={"success": True}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run all six pipelines and return their verdicts with provenance."""
        results = run_faberge(SEED)
        provenance = Provenance(
            package_version=PACKAGE_VERSION,
            seed=SEED,
            input_hash=_input_hash(CODENAME, MissionProvider().brief().objectives, plan),
            wall_time_s=0.0,
        )
        return MissionOutcome(success=True, results=results, provenance=provenance)

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record FABERGÉ's standing lessons."""
        lessons = [
            "anachronistic pigment chemistry is reliable forgery evidence when measured, not assumed",
            "varnish yellowing dates the surface independently of the pigment screen — two channels, one verdict",
            "min-cost flow routes the payload on time only when capacity and deadline are respected",
            "the trainset count is a matching problem, not a guess: minimum path cover bounds the fleet",
            "radiation and mass anomalies fuse into a single prioritized sweep report",
            "flagging a device is not finding it — weighted Gauss-Newton fixes where it sits",
            "the sample royal_egg carries a mass anomaly consistent with a concealed dense core",
        ]
        return Debrief(outcome=outcome, lessons=tuple(lessons))


def register_gadgets(registry: GadgetRegistry | None = None) -> GadgetRegistry:
    """Register FABERGÉ's gadgets with a ``bond_api`` ``GadgetRegistry``.

    If ``registry`` is ``None`` the package's module-level ``gadget_registry``
    is used. Consume-side discovery calls this hook when it is callable; it is
    idempotent (re-registering replaces payloads). Gadgets are opaque payloads.
    """
    target = gadget_registry if registry is None else registry
    target.register(
        FILM,
        {
            "forge_screen": forge.screen_collection,
            "route_cargo": logistics.plan_transfer,
            "sweep_concealment": sweep.fuse_concealment_report,
            "varnish_age": varnish.assess_varnish,
            "circulate_fleet": rolling.fleet_circulation,
            "locate_source": locator.gauss_newton_source,
        },
    )
    return target


#: Gadgets this film contributes to the suite's gadget registry (opaque payloads).
gadget_registry = GadgetRegistry()
register_gadgets(gadget_registry)
