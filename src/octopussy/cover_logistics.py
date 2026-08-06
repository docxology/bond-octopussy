"""Circus-cover smuggling logistics: routing and packing over a rail network.

The circus travels by train. A smuggling operation hides illicit cargo among
the troupe's wagons and moves it along a rail network under that cover. This
module models the problem as **min-cost flow**: each rail segment has a unit
travel cost and a capacity (the number of train slots that can traverse it),
and the smuggler ships ``payload_units`` identical units from a source station
to a sink subject to a deadline.

Two deterministic algorithms are provided:

* :func:`min_cost_flow` — successive shortest paths with Bellman-Ford
  augmenting paths, pushing the cheapest residual path until the demand is
  met or the network is exhausted.
* :func:`golden_ticket_route` — least-cost single-courier route via Dijkstra.

The circus cover itself is handled by :func:`pack_circus_trains`, which packs
payload units into circus wagons of fixed capacity.

Everything is deterministic: tie-breaking is by lexicographic edge order,
costs are integers, and no random draws are made.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

__all__ = [
    "DEFAULT_NETWORK_SEGMENTS",
    "SEGMENT_COUNT",
    "Edge",
    "FlowResult",
    "LogisticsInfeasibleError",
    "RailNetwork",
    "TransferPlan",
    "golden_ticket_route",
    "min_cost_flow",
    "pack_circus_trains",
    "plan_transfer",
]


class LogisticsInfeasibleError(ValueError):
    """Raised when the rail network cannot move the demanded payload."""


@dataclass(frozen=True)
class Edge:
    """A directed rail segment between two stations."""

    origin: str
    destination: str
    travel_time: int  # unit travel cost (minutes)
    capacity: int  # number of train slots
    label: str = ""


def _clean(node: str) -> str:
    node = node.strip()
    if not node:
        raise ValueError("station names must be non-empty")
    return node


def _build_default_segments() -> tuple[Edge, ...]:
    """The FABERGÉ default circus rail corridor.

    The circus train runs east from the Channel fringe through the inland
    garrison to the target station, with a slow scenic branch to the circus
    yard — a decoy that costs more but offers extra capacity for large shows.

    Deliberately no size stated here: :data:`SEGMENT_COUNT` and
    ``RailNetwork().nodes`` are the authority, and a docstring that restated
    them was wrong (it claimed 6 stations; the corridor has 8).
    """
    return (
        Edge("dover", "calais", 40, 4, "ferry"),
        Edge("calais", "amien", 55, 4, "mainline"),
        Edge("amien", "paris", 70, 4, "mainline"),
        Edge("dover", "boulogne", 35, 2, "coastal"),
        Edge("boulogne", "amien", 60, 2, "coastal"),
        Edge("amien", "yard", 25, 3, "spur"),
        Edge("yard", "paris", 90, 3, "spur"),
        Edge("paris", "garrison", 50, 3, "mainline"),
        Edge("garrison", "monastery", 45, 3, "highland"),
    )


#: The default corridor, deterministic at import time.
DEFAULT_NETWORK_SEGMENTS: tuple[Edge, ...] = _build_default_segments()
SEGMENT_COUNT: int = len(DEFAULT_NETWORK_SEGMENTS)


class RailNetwork:
    """A directed rail graph with integer travel costs and segment capacities."""

    def __init__(self, segments: tuple[Edge, ...] | None = None) -> None:
        self._segments: list[Edge] = []
        self._nodes: set[str] = set()
        for segment in segments if segments is not None else DEFAULT_NETWORK_SEGMENTS:
            self.add_segment(segment)

    def add_segment(self, edge: Edge) -> None:
        """Add a validated rail segment."""
        origin, destination = _clean(edge.origin), _clean(edge.destination)
        if origin == destination:
            raise ValueError("a rail segment must connect distinct stations")
        if int(edge.travel_time) <= 0:
            raise ValueError("travel_time must be a positive integer")
        if int(edge.capacity) <= 0:
            raise ValueError("capacity must be a positive integer")
        cleaned = Edge(origin, destination, int(edge.travel_time), int(edge.capacity), edge.label)
        self._segments.append(cleaned)
        self._nodes.update((origin, destination))

    @property
    def nodes(self) -> tuple[str, ...]:
        """Station names, in deterministic sorted order."""
        return tuple(sorted(self._nodes))

    @property
    def segments(self) -> tuple[Edge, ...]:
        """All segments, in insertion order."""
        return tuple(self._segments)


def _residual_capacity(network: RailNetwork, edge_index: int, flows: dict[int, int]) -> int:
    """Forward residual capacity of edge ``edge_index`` given current flows."""
    return network.segments[edge_index].capacity - flows.get(edge_index, 0)


def _augmenting_path(
    network: RailNetwork,
    source: str,
    sink: str,
    flows: dict[int, int],
) -> tuple[list[int], int] | None:
    """Bellman-Ford shortest augmenting path over the residual graph.

    A path is a sequence of "moves": a positive index ``i`` means traverse
    edge ``i`` forward; a negative index ``-(i + 1)`` means traverse edge
    ``i`` in reverse (cancelling one unit of already-shipped flow). Returns
    ``(moves, bottleneck)`` or ``None`` when no residual path exists. Reverse
    moves carry negative reduced cost, so Bellman-Ford is used (deterministic,
    integer-exact, no random or wall-clock behaviour).
    """
    edges = network.segments
    n = len(edges)
    nodes = network.nodes

    # parent[node] = (prev_node, edge_index, reverse_flag)
    parent: dict[str, tuple[str, int, bool] | None] = {node: None for node in nodes}
    dist: dict[str, float] = {node: math.inf for node in nodes}
    dist[source] = 0.0

    def relax(
        move_node: str, move_prev: str, move_index: int, reverse: bool, cost_delta: float, flow_avail: int
    ) -> bool:
        if flow_avail <= 0:
            return False
        candidate = dist[move_prev] + cost_delta
        if candidate < dist[move_node]:
            dist[move_node] = candidate
            parent[move_node] = (move_prev, move_index, reverse)
            return True
        return False

    for _ in range(max(1, len(nodes) - 1)):
        changed = False
        for i in range(n):
            edge = edges[i]
            forward_avail = _residual_capacity(network, i, flows)
            reverse_avail = flows.get(i, 0)
            changed |= relax(edge.destination, edge.origin, i, False, float(edge.travel_time), forward_avail)
            changed |= relax(edge.origin, edge.destination, i, True, float(-edge.travel_time), reverse_avail)
        if not changed:
            break

    if math.isinf(dist[sink]):
        return None

    # Reconstruct the move list from sink back to source.
    moves: list[int] = []
    current = sink
    while current != source:
        entry = parent[current]
        if entry is None:
            return None
        prev, index, reverse = entry
        if reverse:
            moves.append(-(index + 1))
        else:
            moves.append(index)
        current = prev
    moves.reverse()

    bottleneck = None
    for move in moves:
        if move >= 0:
            cap = _residual_capacity(network, move, flows)
        else:
            cap = flows.get(-(move + 1), 0)
        if bottleneck is None or cap < bottleneck:
            bottleneck = cap
    if bottleneck is None or bottleneck <= 0:
        # An empty or zero-capacity path would push zero units forever. Report
        # "no residual path" instead so the caller's loop always terminates.
        return None
    return moves, bottleneck


@dataclass
class FlowResult:
    """The outcome of a *successful* min-cost-flow computation.

    There is deliberately no ``feasible`` flag: :func:`min_cost_flow` either
    returns a result that routed the full demand or raises
    :class:`LogisticsInfeasibleError`. A boolean that is true in every
    constructed instance would be an assertion that can never fail; callers
    that want a non-raising answer use :func:`plan_transfer`, whose
    ``TransferPlan.feasible`` genuinely varies.
    """

    flow_per_edge: dict[int, int]  # edge index -> units moved
    total_cost: int
    total_flow: int


def min_cost_flow(
    network: RailNetwork,
    source: str,
    sink: str,
    demand: int,
) -> FlowResult:
    """Move exactly ``demand`` units from ``source`` to ``sink`` at minimum cost.

    Returns a :class:`FlowResult` whose ``total_flow`` equals ``demand``. When
    the network cannot carry the full demand, raises
    :class:`LogisticsInfeasibleError` reporting how many units *were*
    routable. Successive shortest paths (Bellman-Ford augmenting paths);
    deterministic and integer-exact.

    ``source`` and ``sink`` must be distinct: a self-transfer has no augmenting
    path to push flow along and is rejected as a caller error (:class:`ValueError`)
    rather than silently looping.
    """
    if demand < 0:
        raise ValueError("demand must be non-negative")
    source, sink = _clean(source), _clean(sink)
    if source not in network.nodes or sink not in network.nodes:
        raise ValueError("source and sink must be stations in the network")
    if source == sink:
        raise ValueError("source and sink must be distinct stations")
    if demand == 0:
        return FlowResult({}, 0, 0)

    flows: dict[int, int] = {}
    total_cost = 0
    total_flow = 0
    while total_flow < demand:
        result = _augmenting_path(network, source, sink, flows)
        if result is None:
            raise LogisticsInfeasibleError(
                f"cannot route demand {demand} from {source!r} to {sink!r}: only {total_flow} units feasible"
            )
        moves, bottleneck = result
        push = min(bottleneck, demand - total_flow)
        for move in moves:
            if move >= 0:
                flows[move] = flows.get(move, 0) + push
                total_cost += push * network.segments[move].travel_time
            else:
                index = -(move + 1)
                flows[index] = flows.get(index, 0) - push
        total_flow += push

    return FlowResult(flows, total_cost, total_flow)


@dataclass(frozen=True)
class TransferPlan:
    """A resolved smuggling transfer: routing, deadline check, circus packing."""

    source: str
    sink: str
    payload_units: int
    feasible: bool
    total_cost: int
    edges_used: tuple[tuple[str, str, int], ...]  # (origin, destination, units)
    makespan: int  # longest unit travel time (minutes)
    deadline: int
    slack: int  # deadline - makespan; negative => transfer misses the window
    trains_needed: int
    train_capacity: int


def _decompose_routes(network: RailNetwork, flow: dict[int, int], source: str, sink: str, units: int) -> list[int]:
    """Deterministically split the flow into ``units`` source→sink route lengths.

    Each unit walks forward from ``source`` by following the smallest-labeled
    edge that still has flow, subtracting one unit as it goes. Reproducible
    per-unit total travel times feed the makespan.
    """
    remaining = dict(flow)
    lengths: list[int] = []
    for _ in range(units):
        current = source
        steps = 0
        while current != sink:
            candidates = sorted(
                i for i, e in enumerate(network.segments) if e.origin == current and remaining.get(i, 0) > 0
            )
            if not candidates:
                break
            index = candidates[0]
            remaining[index] -= 1
            current = network.segments[index].destination
            steps += network.segments[index].travel_time
        lengths.append(steps)
    return lengths


def plan_transfer(
    network: RailNetwork,
    source: str,
    sink: str,
    payload_units: int,
    *,
    deadline: int,
    train_capacity: int = 2,
) -> TransferPlan:
    """Route ``payload_units`` from ``source`` to ``sink`` by the deadline.

    Builds the transfer manifest: the min-cost flow, the per-unit makespan,
    the deadline slack, and the number of circus trains required to carry the
    payload at the given wagon capacity.

    This is the *non-raising* entry point. A network that cannot carry the
    payload is a legitimate mission answer, not an error, so
    :class:`LogisticsInfeasibleError` is caught and reported as a plan with
    ``feasible=False``, zero cost, no routed edges, and ``slack=-deadline``
    (the whole window is missed). Caller errors — an unknown station, a
    negative payload, a self-transfer — still raise :class:`ValueError`: only
    the infeasibility signal is absorbed here.
    """
    try:
        flow: FlowResult | None = min_cost_flow(network, source, sink, payload_units)
    except LogisticsInfeasibleError:
        flow = None
    if flow is None:
        return TransferPlan(source, sink, payload_units, False, 0, (), 0, deadline, -deadline, 0, train_capacity)

    lengths = _decompose_routes(network, flow.flow_per_edge, source, sink, payload_units)
    makespan = max(lengths) if lengths else 0
    edges_used = tuple(
        (network.segments[i].origin, network.segments[i].destination, amount)
        for i, amount in sorted(flow.flow_per_edge.items())
        if amount > 0
    )
    trains, _ = pack_circus_trains(payload_units, train_capacity)
    return TransferPlan(
        source=source,
        sink=sink,
        payload_units=payload_units,
        feasible=True,
        total_cost=flow.total_cost,
        edges_used=edges_used,
        makespan=makespan,
        deadline=deadline,
        slack=deadline - makespan,
        trains_needed=trains,
        train_capacity=train_capacity,
    )


def golden_ticket_route(network: RailNetwork, source: str, sink: str) -> tuple[str, ...]:
    """Least-cost single-unit route (Dijkstra), returned as a station chain."""
    source, sink = _clean(source), _clean(sink)
    if source not in network.nodes or sink not in network.nodes:
        raise LogisticsInfeasibleError(f"no route from {source!r} to {sink!r}")
    distances: dict[str, float] = {n: math.inf for n in network.nodes}
    previous: dict[str, str | None] = {n: None for n in network.nodes}
    distances[source] = 0.0
    heap: list[tuple[float, str]] = [(0.0, source)]
    while heap:
        d, node = heapq.heappop(heap)
        if d > distances[node]:
            continue
        for edge in (e for e in network.segments if e.origin == node):
            candidate = d + edge.travel_time
            if candidate < distances[edge.destination]:
                distances[edge.destination] = candidate
                previous[edge.destination] = node
                heapq.heappush(heap, (candidate, edge.destination))
    if math.isinf(distances[sink]):
        raise LogisticsInfeasibleError(f"no route from {source!r} to {sink!r}")
    path: list[str] = [sink]
    while path[-1] != source:
        prev = previous[path[-1]]
        if prev is None:
            raise LogisticsInfeasibleError(f"no route from {source!r} to {sink!r}")
        path.append(prev)
    path.reverse()
    return tuple(path)


def pack_circus_trains(payload_units: int, train_capacity: int) -> tuple[int, tuple[int, ...]]:
    """Pack payload units into circus trains of fixed wagon capacity.

    Returns ``(number_of_trains, load_per_train)``. A deterministic greedy
    fill: trains are loaded to capacity except possibly the last one.
    """
    if payload_units < 0:
        raise ValueError("payload_units must be non-negative")
    if int(train_capacity) <= 0:
        raise ValueError("train_capacity must be a positive integer")
    capacity = int(train_capacity)
    if payload_units == 0:
        return 0, ()
    num_trains = (payload_units + capacity - 1) // capacity
    loads = [capacity] * (payload_units // capacity)
    remainder = payload_units % capacity
    if remainder:
        loads.append(remainder)
    return num_trains, tuple(loads)
