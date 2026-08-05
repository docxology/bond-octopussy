"""Tests for :mod:`octopussy.cover_logistics` (min-cost flow logistics)."""

from __future__ import annotations

import pytest

from octopussy import cover_logistics as cl


def _net() -> cl.RailNetwork:
    return cl.RailNetwork()


def test_edge_validation_errors():
    net = cl.RailNetwork(())
    with pytest.raises(ValueError):
        net.add_segment(cl.Edge("a", "a", 5, 2))  # self loop
    with pytest.raises(ValueError):
        net.add_segment(cl.Edge("a", "b", 0, 2))  # non-positive time
    with pytest.raises(ValueError):
        net.add_segment(cl.Edge("a", "b", 5, 0))  # non-positive capacity
    with pytest.raises(ValueError):
        net.add_segment(cl.Edge("  ", "b", 5, 2))  # blank node


def test_network_nodes_sorted():
    net = _net()
    assert net.nodes == ("amien", "boulogne", "calais", "dover", "garrison", "monastery", "paris", "yard")
    assert len(net.segments) == cl.SEGMENT_COUNT == 9


def test_min_cost_flow_zero_demand():
    result = cl.min_cost_flow(_net(), "dover", "monastery", 0)
    assert result.total_flow == 0 and result.total_cost == 0 and result.flow_per_edge == {}


def test_min_cost_flow_rejects_self_transfer():
    """A source==sink request must raise, not spin forever.

    Regression: the augmenting-path search returned an empty move list with a
    zero bottleneck for a self-transfer, so ``min_cost_flow`` pushed zero units
    per iteration and never terminated.
    """
    with pytest.raises(ValueError, match="distinct"):
        cl.min_cost_flow(_net(), "dover", "dover", 3)


def test_plan_transfer_rejects_self_transfer():
    with pytest.raises(ValueError, match="distinct"):
        cl.plan_transfer(_net(), "dover", "dover", 3, deadline=400)


def test_min_cost_flow_negative_demand():
    with pytest.raises(ValueError):
        cl.min_cost_flow(_net(), "dover", "monastery", -1)


def test_min_cost_flow_unknown_node():
    with pytest.raises(ValueError):
        cl.min_cost_flow(_net(), "dover", "nowhere", 1)


def test_min_cost_flow_success():
    result = cl.min_cost_flow(_net(), "dover", "monastery", 3)
    assert result.total_flow == 3
    assert result.total_cost > 0
    # Every routed edge must respect its declared capacity.
    segments = _net().segments
    assert all(units <= segments[index].capacity for index, units in result.flow_per_edge.items())


def test_min_cost_flow_infeasible():
    # Demand beyond total corridor capacity must raise.
    with pytest.raises(cl.LogisticsInfeasibleError):
        cl.min_cost_flow(_net(), "dover", "monastery", 100)


def test_plan_transfer_feasible():
    plan = cl.plan_transfer(_net(), "dover", "monastery", 3, deadline=400, train_capacity=2)
    assert plan.feasible
    assert plan.total_cost > 0
    assert plan.makespan > 0
    assert plan.slack >= 0
    assert plan.trains_needed == 2
    assert plan.edges_used
    assert plan.train_capacity == 2


def test_plan_transfer_missed_deadline():
    plan = cl.plan_transfer(_net(), "dover", "monastery", 3, deadline=50)
    assert plan.feasible
    assert plan.slack < 0


def test_plan_transfer_infeasible():
    plan = cl.plan_transfer(_net(), "dover", "monastery", 100, deadline=999)
    assert not plan.feasible
    assert plan.slack == -999


def test_golden_ticket_route():
    route = cl.golden_ticket_route(_net(), "dover", "monastery")
    assert route[0] == "dover" and route[-1] == "monastery"


def test_golden_ticket_route_unreachable():
    net = cl.RailNetwork((cl.Edge("a", "b", 5, 2),))
    with pytest.raises(cl.LogisticsInfeasibleError):
        cl.golden_ticket_route(net, "a", "c")


def test_pack_circus_trains():
    assert cl.pack_circus_trains(0, 2) == (0, ())
    assert cl.pack_circus_trains(3, 2) == (2, (2, 1))
    assert cl.pack_circus_trains(4, 2) == (2, (2, 2))
    with pytest.raises(ValueError):
        cl.pack_circus_trains(-1, 2)
    with pytest.raises(ValueError):
        cl.pack_circus_trains(3, 0)


def test_default_corridor_routes_eastward():
    net = _net()
    # The cheap mainline reaches the monastery with plenty of capacity.
    plan = cl.plan_transfer(net, "dover", "monastery", 3, deadline=400)
    assert plan.feasible
    assert all(e[0] == "dover" for e in plan.edges_used) is False  # routed via corridor interior
