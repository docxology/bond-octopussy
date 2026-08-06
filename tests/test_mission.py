"""Tests for :mod:`octopussy.mission` (BOND-API MissionProvider + gadgets)."""

from __future__ import annotations

import os

import pytest

from bond_api import load_provider
from bond_api.protocol import ReconRequest, MissionProvider as Protocol
from bond_api.registry import GadgetRegistry
from octopussy.mission import (
    CODENAME,
    FILM,
    SEED,
    MissionProvider,
    _input_hash,
    gadget_registry,
    run_faberge,
)

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))


def test_mission_constants():
    assert FILM == "octopussy"
    assert CODENAME == "FABERGÉ"
    assert SEED == 7


def test_provider_discoverable_via_protocol():
    provider = load_provider("octopussy", search_paths=[SRC])
    assert isinstance(provider, Protocol)
    assert provider.film == "octopussy"


def test_provider_methods_return_protocol_types():
    provider = MissionProvider()
    brief = provider.brief()
    assert brief.film == "octopussy" and brief.codename == "FABERGÉ"
    assert len(brief.objectives) == 3
    report = provider.recon(ReconRequest("scope"))
    assert report.findings
    plan = provider.plan(brief)
    assert plan.steps and plan.steps[0].name == "forge_screen"
    outcome = provider.execute(plan)
    assert outcome.success
    debrief = provider.debrief(outcome)
    assert debrief.lessons


def test_run_faberge_structure():
    results = run_faberge(SEED)
    assert {"forgery", "logistics", "concealment", "varnish", "rolling_stock", "source_locator"} == set(results)
    assert results["forgery"]["screened"] == 4
    assert results["logistics"]["feasible"] is True
    assert results["concealment"]["flagged"]
    assert results["varnish"]["fake_verdict"] == "too_young"
    assert results["rolling_stock"]["trainsets"] == 2
    assert results["source_locator"]["converged"] is True


def test_run_faberge_deterministic():
    a = run_faberge(9)
    b = run_faberge(9)
    assert a["concealment"]["hotspots"] == b["concealment"]["hotspots"]
    assert a["varnish"]["genuine_estimated_age"] == b["varnish"]["genuine_estimated_age"]
    assert a["rolling_stock"]["chains"] == b["rolling_stock"]["chains"]
    assert a["source_locator"]["estimated_position"] == b["source_locator"]["estimated_position"]


def test_input_hash_stable():
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    h1 = _input_hash(CODENAME, provider.brief().objectives, plan)
    h2 = _input_hash(CODENAME, provider.brief().objectives, plan)
    assert h1 == h2 and len(h1) == 64


def test_input_hash_changes_with_objectives():
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    h = _input_hash(CODENAME, provider.brief().objectives, plan)
    other = _input_hash(CODENAME, ("different",), plan)
    assert h != other


def test_gadgets_registered():
    assert isinstance(gadget_registry, GadgetRegistry)
    assert gadget_registry.gadgets_for("octopussy") == (
        "forge_screen",
        "route_cargo",
        "sweep_concealment",
        "varnish_age",
        "circulate_fleet",
        "locate_source",
    )
    assert gadget_registry.contains("octopussy", "forge_screen")
    assert gadget_registry.contains("octopussy", "locate_source")


def test_register_gadgets_hook():
    from octopussy.mission import register_gadgets

    fresh = GadgetRegistry()
    returned = register_gadgets(fresh)
    assert returned is fresh
    assert fresh.gadgets_for("octopussy") == gadget_registry.gadgets_for("octopussy")
    # idempotent — re-registering on the module registry keeps the same set.
    register_gadgets(gadget_registry)
    assert len(gadget_registry.gadgets_for("octopussy")) == 6


def test_gadget_registry_drop():
    reg = GadgetRegistry()
    reg.register("octopussy", {"x": 1})
    assert reg.lookup("octopussy", "x") == 1
    with pytest.raises(KeyError):
        reg.drop("octopussy", "missing")
    reg.drop("octopussy", "x")
    assert reg.films() == ()


def test_mission_uses_no_infrastructure_imports():
    from octopussy import (
        concealment_sweep,
        cover_logistics,
        forgery_detection,
        rolling_stock,
        source_locator,
        varnish_ageing,
    )

    for module in (
        forgery_detection,
        cover_logistics,
        concealment_sweep,
        varnish_ageing,
        rolling_stock,
        source_locator,
    ):
        source = module.__file__ or ""
        text = open(source, encoding="utf-8").read()
        assert "import infrastructure" not in text
        assert "from infrastructure" not in text
        assert "import bond_api" not in text
        assert "from bond_api" not in text


def test_pipeline_registry_matches_run_faberge_keys():
    """PIPELINES is the contract; result keys must equal it exactly."""
    from octopussy.mission import PIPELINES, PIPELINE_COUNT

    results = run_faberge(SEED)
    assert tuple(results) == PIPELINES
    assert PIPELINE_COUNT == len(PIPELINES) == 6


def test_sweep_constants_are_derived_not_restated():
    from octopussy.mission import SWEEP_DETECTORS, SWEEP_GRID

    assert SWEEP_DETECTORS == SWEEP_GRID.nx * SWEEP_GRID.ny
    brief = MissionProvider().brief()
    sweep_asset = next(a for a in brief.assets if a.name == "sweep")
    assert sweep_asset.payload["detectors"] == SWEEP_DETECTORS


def test_source_block_reports_uncertainty_alongside_error():
    """A position fix without an uncertainty is an unfalsifiable claim."""
    source = run_faberge(SEED)["source_locator"]
    assert source["position_std_m"] > 0.0
    assert source["error_m"] >= 0.0
    assert source["iterations"] >= 1


def test_varnish_pipeline_actually_reads_the_exhibit():
    """The manuscript says the varnish channel dates *exhibit* artifacts.

    It used to be false: the varnish block synthesized its own transmittance
    curves from a bare band grid and never touched forge.DEFAULT_EXHIBIT, so
    the 'same objects, second observable' claim had no code behind it. Bind the
    claim to the exhibit record, and make it fail if the coupling is cut.
    """
    import numpy as np

    from octopussy import forgery_detection as fg
    from octopussy import varnish_ageing as va
    from octopussy.mission import _VARNISH_CURRENT, _VARNISH_NOISE, _unvarnished_reference, _varnish_rng

    block = run_faberge(SEED)["varnish"]
    exhibit = {a.name: a for a in fg.DEFAULT_EXHIBIT}
    for key in ("genuine_artifact", "fake_artifact"):
        assert block[key] in exhibit, f"{key} names an artifact outside the exhibit"
    genuine = exhibit[block["genuine_artifact"]]
    # The claimed year is read off the exhibit, not restated in mission.py.
    assert block["claimed_year"] == genuine.claimed_year
    assert block["genuine_true_age"] == float(block["current_year"] - genuine.claimed_year)

    # The reference spectrum really is that artifact's substrate.
    substrate = tuple((n, w) for n, w in genuine.mixture if fg.PIGMENT_LIBRARY[n].category != "varnish")
    assert substrate != genuine.mixture, "fixture precondition: the artifact has a varnish layer to strip"
    reference = _unvarnished_reference(genuine)
    np.testing.assert_allclose(reference, fg.mix_spectrum(substrate))

    # Bind the *published number* to that reference: replay the channel's own
    # generator against the exhibit substrate and require the same age.
    def _dated(ref):
        measured = va.measure_varnished_surface(
            ref, block["genuine_true_age"], rng=_varnish_rng(SEED), noise_std=_VARNISH_NOISE
        )
        return round(
            float(va.date_varnished_surface(measured, ref, genuine.claimed_year, _VARNISH_CURRENT).estimated_age), 1
        )

    assert _dated(reference) == block["genuine_estimated_age"]
    # Positive control: the reference is load-bearing. A generic flat substrate
    # — which is what the pipeline used before it read the exhibit at all —
    # produces a different age, so the assertion above is not vacuous.
    flat = np.full(reference.size, 0.6)
    assert _dated(flat) != block["genuine_estimated_age"]


def test_varnish_and_forgery_share_one_band_grid():
    """The two grids are equal by construction — bind them before they aren't.

    The varnish channel multiplies an exhibit spectrum (on the forgery module's
    grid) by a transmittance (on the varnish module's grid) band for band, and
    divides them again to recover the film. If the grids ever diverged, that
    product would be silently meaningless rather than an error.
    """
    import numpy as np

    from octopussy import forgery_detection as fg
    from octopussy import varnish_ageing as va

    np.testing.assert_array_equal(va.DEFAULT_BANDS, fg.WAVELENGTH_BANDS)


def test_bands_are_a_single_shared_definition():
    """C3: one band grid serves both optical channels — by identity, not luck.

    The prior version duplicated ``np.linspace(320, 760, 24)`` in two modules
    and relied on an array-equality assert downstream to catch drift. Both
    modules now import the same array object from ``octopussy._bands``, so a
    divergence is impossible rather than merely asserted-away.
    """
    from octopussy import _bands
    from octopussy import forgery_detection as fg
    from octopussy import varnish_ageing as va

    assert fg.WAVELENGTH_BANDS is _bands.WAVELENGTH_BANDS
    assert va.DEFAULT_BANDS is _bands.WAVELENGTH_BANDS
    assert fg.BAND_MIN_NM == _bands.BAND_MIN_NM and fg.BAND_COUNT == _bands.BAND_COUNT


def test_varnish_missing_artifact_fails_loudly():
    from octopussy.mission import _exhibit_artifact

    with pytest.raises(KeyError, match="no surface to date"):
        _exhibit_artifact("not_in_the_exhibit")


def test_unvarnished_reference_rejects_a_varnish_only_artifact():
    from octopussy import forgery_detection as fg
    from octopussy.mission import _unvarnished_reference

    with pytest.raises(ValueError, match="no substrate"):
        _unvarnished_reference(fg.Artifact("bare", 1900, (("shellac_varnish", 1.0),)))


def test_varnish_reports_its_own_error_bar_and_the_asymmetry():
    """A single verdict without an ensemble is an unfalsifiable claim.

    The results section reports the fresh coat as decisively rejected and the
    century-old surface as undecidable — every verdict reachable from it by
    measurement noise alone. Those are the two properties that make the honest
    reading honest, so assert both.
    """
    from octopussy import varnish_ageing as va

    block = run_faberge(SEED)["varnish"]
    trials = block["trials"]
    assert trials >= 2
    # Fresh coat: rejected in every realization, with a tight spread.
    assert block["fake_verdict"] == "too_young"
    assert block["fake_rejected_trials"] == trials
    assert block["fake_age_std"] < block["tolerance_years"]
    # Century-old surface: the spread exceeds the tolerance it is judged by,
    # and measurement noise alone reaches every verdict the classifier can
    # emit — which is the claim the results and scope sections now make, so it
    # must be bound here rather than asserted in prose.
    assert block["genuine_age_std"] > block["tolerance_years"]
    assert block["genuine_consistent_trials"] < trials
    assert block["genuine_age_min"] < block["genuine_age_max"]
    assert block["genuine_age_max"] - block["genuine_age_min"] > block["tolerance_years"]
    assert block["genuine_verdicts_seen"] == len(va.AgeVerdict)
    for level in va.AgeVerdict:
        assert f"{level.value}×" in block["genuine_verdict_spread"]


def test_cover_check_actually_compares_the_two_pipelines():
    """The conclusion ties the routed plan to the circus fleet — prove it.

    The rolling-stock matching runs over its own trip fixture, so on its own it
    says nothing about the min-cost flow. These fields are the comparison, and
    they must be computed from the live logistics output rather than restated.
    """
    results = run_faberge(SEED)
    logistics_out = results["logistics"]
    rolling_out = results["rolling_stock"]
    assert rolling_out["trains_needed"] == logistics_out["trains_needed"]
    assert rolling_out["routed_legs"] == len({(o, d) for o, d, _ in logistics_out["edges_used"]})
    assert rolling_out["corridor_covered"] is True
    assert rolling_out["uncovered_legs"] == []
    assert rolling_out["fleet_sufficient"] is True
    assert rolling_out["trains_needed"] <= rolling_out["trainsets"]


def test_cover_check_goes_false_when_the_schedule_stops_covering_the_route():
    """Negative control, through the production path.

    A green "corridor_covered: true" proves nothing unless the field can be
    false, so re-run `run_faberge` itself against a schedule missing the last
    corridor leg. A hard-wired true would survive the assertions above; it
    cannot survive this one.
    """
    from octopussy.mission import _ROLLING_TRIPS

    crippled = tuple(t for t in _ROLLING_TRIPS if (t.origin, t.destination) != ("garrison", "monastery"))
    assert len(crippled) < len(_ROLLING_TRIPS), "fixture precondition: that leg is in the schedule"

    rolling_out = run_faberge(SEED, trips=crippled)["rolling_stock"]
    assert rolling_out["corridor_covered"] is False
    assert rolling_out["uncovered_legs"] == [["garrison", "monastery"]]


def test_fleet_sufficiency_goes_false_when_the_fleet_is_too_small():
    """The other half of the cover check must also be falsifiable."""
    from octopussy.mission import _ROLLING_TRIPS

    lone = (_ROLLING_TRIPS[0],)
    rolling_out = run_faberge(SEED, trips=lone)["rolling_stock"]
    assert rolling_out["trainsets"] == 1
    assert rolling_out["trains_needed"] > rolling_out["trainsets"]
    assert rolling_out["fleet_sufficient"] is False


def test_debrief_lessons_cover_every_pipeline_family():
    from octopussy.mission import PIPELINES

    provider = MissionProvider()
    debrief = provider.debrief(provider.execute(provider.plan(provider.brief())))
    joined = " ".join(debrief.lessons).lower()
    for keyword in ("pigment", "varnish", "min-cost flow", "matching", "sweep", "gauss-newton"):
        assert keyword in joined, f"debrief never mentions {keyword}"
    assert len(debrief.lessons) >= len(PIPELINES)
