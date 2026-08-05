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
