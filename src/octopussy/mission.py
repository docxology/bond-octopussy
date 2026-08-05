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
    "FILM",
    "CODENAME",
    "SEED",
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

#: Scenario parameters for the execute stage (deterministic scenario).
_FORGERY_NOISE = 0.02
_LOGISTICS_SOURCE = "dover"
_LOGISTICS_SINK = "monastery"
_LOGISTICS_UNITS = 3
_LOGISTICS_DEADLINE = 400
_LOGISTICS_CAPACITY = 2
_SWEEP_GRID = sweep.SweepGrid((0.0, 0.0), 2.0, 10, 10)
_SWEEP_BACKGROUND = 40.0
_SWEEP_SOURCE = sweep.RadiationSource((7.0, 7.0), 800.0)
_SWEEP_THRESHOLD = 3.0

# Varnish-ageing scenario: claimed provenance vs a freshly-varnished fake.
_VARNISH_CLAIMED = 1910
_VARNISH_CURRENT = 2026
_VARNISH_FAKE_AGE = 3.0
_VARNISH_NOISE = 0.02

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


def _input_hash(codename: str, objectives: tuple[str, ...], plan: MissionPlan) -> str:
    """Deterministic sha256 fingerprint of the mission's defining inputs."""
    payload = {
        "codename": codename,
        "objectives": list(objectives),
        "steps": [{"name": step.name, "action": step.action, "params": step.params} for step in plan.steps],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_faberge(seed: int = SEED) -> dict[str, object]:
    """Run the three investigative pipelines; return structured results.

    Deterministic under the fixed ``seed``: the forgery screen, the
    logistics plan, and the concealment sweep are all computed (never faked),
    and the returned dict is JSON-serializable for mission reports.
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
    positions, counts = sweep.simulate_sweep(_SWEEP_GRID, _SWEEP_BACKGROUND, (_SWEEP_SOURCE,), seed=seed)
    background = sweep.estimate_background(counts)
    anomaly = sweep.anomaly_map(counts, background)
    hits = sweep.detect_hotspots(counts, anomaly, _SWEEP_THRESHOLD)
    report = sweep.fuse_concealment_report(hits, sweep.DEFAULT_CONTAINERS)
    concealment = {
        "grid_size": int(_SWEEP_GRID.nx * _SWEEP_GRID.ny),
        "hotspots": [{"position": list(h.position), "score": round(float(h.score), 3)} for h in hits],
        "suspicious": [
            {"kind": e.kind, "name": e.name, "score": round(float(e.score), 3), "detail": e.detail}
            for e in report.entries
        ],
        "flagged": list(report.flagged),
        "worst": report.worst.name if report.worst else None,
    }

    # 4) Varnish ageing — date the exhibit's varnish against its claimed era.
    bands = varnish.DEFAULT_BANDS
    genuine_T = np.clip(
        varnish.varnish_transmittance(bands, float(_VARNISH_CURRENT - _VARNISH_CLAIMED))
        + rng.normal(0.0, _VARNISH_NOISE, size=bands.size),
        0.0,
        1.0,
    )
    fake_T = np.clip(
        varnish.varnish_transmittance(bands, _VARNISH_FAKE_AGE) + rng.normal(0.0, _VARNISH_NOISE, size=bands.size),
        0.0,
        1.0,
    )
    genuine_assess = varnish.assess_varnish(genuine_T, _VARNISH_CLAIMED, _VARNISH_CURRENT)
    fake_assess = varnish.assess_varnish(fake_T, _VARNISH_CLAIMED, _VARNISH_CURRENT)
    varnish_block = {
        "claimed_year": _VARNISH_CLAIMED,
        "current_year": _VARNISH_CURRENT,
        "genuine_estimated_age": round(float(genuine_assess.estimated_age), 1),
        "genuine_verdict": genuine_assess.verdict.value,
        "fake_estimated_age": round(float(fake_assess.estimated_age), 1),
        "fake_verdict": fake_assess.verdict.value,
        "fake_closeness": round(float(fake_assess.closeness), 3),
    }

    # 5) Rolling-stock circulation — how many circus trainsets cover the trips.
    fleet = rolling.fleet_circulation(_ROLLING_TRIPS, _ROLLING_TURNAROUND)
    depot = rolling.kuhn_munkres([list(row) for row in _DEPOT_COST])
    rolling_block = {
        "trips": fleet.trips,
        "trainsets": fleet.trainsets,
        "matching_edges": fleet.matching_edges,
        "deadhead_minutes": fleet.deadhead_minutes,
        "turnaround": fleet.turnaround,
        "chains": [list(chain) for chain in fleet.chains],
        "depot_assignment": [[int(r), int(c), round(float(cost), 1)] for r, c, cost in depot],
        "depot_assignment_cost": float(sum(cost for _, _, cost in depot)),
    }

    # 6) Source localization — locate the concealed emitter from the sweep.
    localized = locator.locate_from_sweep(_SWEEP_GRID, counts, background)
    position_error = (
        (localized.position[0] - _SWEEP_SOURCE.position[0]) ** 2
        + (localized.position[1] - _SWEEP_SOURCE.position[1]) ** 2
    ) ** 0.5
    source_block = {
        "estimated_position": [round(float(p), 3) for p in localized.position],
        "true_position": list(_SWEEP_SOURCE.position),
        "error_m": round(float(position_error), 3),
        "intensity": round(float(localized.intensity), 1),
        "residual": round(float(localized.residual_norm), 3),
        "converged": localized.converged,
        "iterations": localized.iterations,
    }

    return {
        "forgery": forgery,
        "logistics": logistics_results,
        "concealment": concealment,
        "varnish": varnish_block,
        "rolling_stock": rolling_block,
        "source_locator": source_block,
    }


class MissionProvider:  # noqa: N801 — class name is fixed by the discovery contract
    """FABERGÉ: detect forgeries, route the cargo, and sweep for the device."""

    film = FILM

    def brief(self) -> MissionBrief:
        """Declare the FABERGÉ mission: three investigative objectives."""
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
                Asset(kind="scenario", name="sweep", payload={"detectors": int(_SWEEP_GRID.nx * _SWEEP_GRID.ny)}),
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
                    detail=f"{int(_SWEEP_GRID.nx * _SWEEP_GRID.ny)} detectors in the concealed-device sweep",
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
                Step(name="varnish_age", action="yellowing_kinetics", params={"claimed": _VARNISH_CLAIMED}),
                Step(name="rolling_stock", action="fleet_circulation", params={"turnaround": _ROLLING_TURNAROUND}),
                Step(name="source_locator", action="gauss_newton_localization", params={"tolerance": 1e-6}),
                Step(name="verify", action="collect_provenance", params={"success": True}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the three pipelines and return their verdicts with provenance."""
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
            "min-cost flow routes the payload on time only when capacity and deadline are respected",
            "radiation and mass anomalies fuse into a single prioritized sweep report",
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
