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


def test_solver_goes_through_public_accessors():
    """A network exposing only the public surface must still solve.

    Regression (C2): the solver used to reach into ``network._segments`` /
    ``network._nodes`` / ``network._out``, so any future wrapper or subclass
    that satisfies the public ``.segments`` / ``.nodes`` surface silently broke
    it. This proxy delegates exclusively through those public properties; if
    any solver path ever reads a private attribute again, the proxy (which has
    none) fails instead of returning wrong numbers.
    """

    class ProxyRail(cl.RailNetwork):
        def __init__(self) -> None:
            self._inner = cl.RailNetwork()

        @property
        def nodes(self) -> tuple[str, ...]:
            return self._inner.nodes

        @property
        def segments(self) -> tuple[cl.Edge, ...]:
            return self._inner.segments

        def add_segment(self, edge: cl.Edge) -> None:
            self._inner.add_segment(edge)

    net = ProxyRail()
    flow = cl.min_cost_flow(net, "dover", "monastery", 3)
    assert flow.total_flow == 3
    plan = cl.plan_transfer(net, "dover", "monastery", 3, deadline=400)
    assert plan.feasible
    assert plan.makespan > 0
    route = cl.golden_ticket_route(net, "dover", "monastery")
    assert route[0] == "dover" and route[-1] == "monastery"


def test_min_cost_flow_with_arc_cancellation_is_conserving():
    """A network whose optimum re-routes flow must still be node-conserving.

    Successive shortest paths can cancel an earlier augmenting path's flow
    along a reverse (negative-cost) arc — the V4 reverse-move path. The raw
    flow dict may even carry a zeroed edge after a cancellation; the flow it
    represents must conserve mass at every interior node and route exactly the
    demand, or the reported cost and edges are meaningless.
    """
    from collections import defaultdict

    net = cl.RailNetwork(
        (
            cl.Edge("s", "a", 2, 1),
            cl.Edge("s", "b", 4, 1),
            cl.Edge("a", "t", 3, 2),
            cl.Edge("b", "t", 1, 1),
            cl.Edge("a", "b", 1, 2),
            cl.Edge("b", "a", 3, 2),
            cl.Edge("s", "t", 7, 1),
        )
    )
    result = cl.min_cost_flow(net, "s", "t", 2)
    assert result.total_flow == 2
    assert result.total_cost == 11
    balance: dict[str, int] = defaultdict(int)
    for idx, units in result.flow_per_edge.items():
        if units == 0:
            continue
        edge = net.segments[idx]
        balance[edge.origin] -= units
        balance[edge.destination] += units
    assert balance["s"] == -2
    assert balance["t"] == 2
    for node, net_in in balance.items():
        if node not in ("s", "t"):
            assert net_in == 0, f"{node} is not flow-conserving in {dict(result.flow_per_edge)}"


def test_golden_ticket_route_disconnected_sink():
    """A sink that is a station but unreachable must raise, not crash (V4)."""
    net = cl.RailNetwork((cl.Edge("a", "b", 5, 2), cl.Edge("c", "d", 3, 2)))
    with pytest.raises(cl.LogisticsInfeasibleError):
        cl.golden_ticket_route(net, "a", "c")


def test_golden_ticket_route_skips_stale_heap_entries():
    """Dijkstra must ignore a node whose old (larger) distance is popped late."""
    net = cl.RailNetwork(
        (
            cl.Edge("s", "x", 1, 2),
            cl.Edge("s", "y", 5, 2),
            cl.Edge("x", "y", 1, 2),
            cl.Edge("y", "t", 1, 2),
        )
    )
    route = cl.golden_ticket_route(net, "s", "t")
    assert route == ("s", "x", "y", "t")
