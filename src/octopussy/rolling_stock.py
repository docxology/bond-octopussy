"""Rolling-stock circulation: scheduling the circus trainset fleet.

The circus runs a fixed set of rail *trips* (departure station, arrival
station, departure time, arrival time). A trainset that finishes a trip at
station X at time ``t`` can only take a next trip departing from X at
``t + turnaround`` or later. The fleet-planning questions are:

1. **How few trainsets suffice?** With ``n`` trips, the minimum number of
   trainsets equals ``n - M`` where ``M`` is the size of a maximum matching
   in the trip-compatibility bipartite graph (minimum path cover theorem).
   :func:`maximum_matching` computes it with Hopcroft–Karp; :func:`fleet_circulation`
   decomposes the matching into the actual trainset itineraries.
2. **How should trainsets be assigned to routes at minimum deadhead cost?**
   :func:`kuhn_munkres` solves the classic minimum-cost assignment problem
   (Hungarian algorithm) over a square cost matrix.

Both algorithms are deterministic: iteration order is fixed, no random state,
integer-exact arithmetic for the matching.

Pure domain logic (stdlib only), no ``infrastructure`` or ``bond_api`` imports.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "FleetPlan",
    "Trip",
    "can_follow",
    "compatibility_edges",
    "fleet_circulation",
    "kuhn_munkres",
    "maximum_matching",
    "minimum_trainsets",
]


@dataclass(frozen=True)
class Trip:
    """A scheduled rail trip with fixed stations and integer minutes."""

    trip_id: str
    origin: str
    destination: str
    depart: int
    arrive: int

    def __post_init__(self) -> None:
        if not self.trip_id.strip():
            raise ValueError("Trip.trip_id must be a non-empty string")
        if not self.origin.strip() or not self.destination.strip():
            raise ValueError("Trip stations must be non-empty strings")
        if self.origin == self.destination:
            raise ValueError("a trip must connect distinct stations")
        if self.depart < 0 or self.arrive < 0:
            raise ValueError("trip times must be non-negative minutes")
        if self.arrive <= self.depart:
            raise ValueError("a trip's arrival must be after its departure")


def can_follow(first: Trip, second: Trip, turnaround: int = 20) -> bool:
    """Whether one trainset can work ``first`` then ``second``."""
    if turnaround < 0:
        raise ValueError("turnaround must be non-negative")
    return second.origin == first.destination and second.depart >= first.arrive + turnaround


def compatibility_edges(trips: tuple[Trip, ...], turnaround: int = 20) -> tuple[tuple[int, ...], ...]:
    """Bipartite adjacency: for each left trip index, successor trip indices."""
    edges: list[tuple[int, ...]] = []
    for first in trips:
        successors = tuple(i for i, second in enumerate(trips) if can_follow(first, second, turnaround))
        edges.append(successors)
    return tuple(edges)


def maximum_matching(adjacency: tuple[tuple[int, ...], ...]) -> dict[int, int]:
    """Maximum bipartite matching via Hopcroft–Karp; returns left->right map.

    Deterministic: BFS levels and DFS augmentations iterate in index order,
    so the returned matching is reproducible for a given input.
    """
    n_left = len(adjacency)
    pair_left: dict[int, int] = {}  # left -> right
    pair_right: dict[int, int] = {}  # right -> left
    distances: dict[int, int] = {}

    def dfs(left: int) -> bool:
        for right in adjacency[left]:
            match = pair_right.get(right)
            if match is None or (match in distances and distances[match] == distances[left] + 1 and dfs(match)):
                pair_left[left] = right
                pair_right[right] = left
                return True
        distances[left] = -1
        return False

    while True:
        # BFS: build the layered graph of shortest augmenting paths.
        distances = {}
        queue: list[int] = []
        for left in range(n_left):
            if left not in pair_left:
                distances[left] = 0
                queue.append(left)
        found_free_right = False
        head = 0
        while head < len(queue):
            left = queue[head]
            head += 1
            for right in adjacency[left]:
                match = pair_right.get(right)
                if match is None:
                    found_free_right = True
                elif match not in distances:
                    distances[match] = distances[left] + 1
                    queue.append(match)
        if not found_free_right:
            break
        # DFS: augment along every unmatched left node.
        for left in range(n_left):
            if left not in pair_left:
                dfs(left)
    return dict(pair_left)


def minimum_trainsets(trips: tuple[Trip, ...], turnaround: int = 20) -> int:
    """Minimum number of trainsets by the min-path-cover theorem."""
    matching = maximum_matching(compatibility_edges(trips, turnaround))
    return len(trips) - len(matching)


@dataclass(frozen=True)
class FleetPlan:
    """A resolved fleet circulation: trainsets, itineraries, deadhead."""

    trips: int
    trainsets: int
    matching_edges: int
    chains: tuple[tuple[str, ...], ...]  # trip_id sequences per trainset
    deadhead_minutes: int
    turnaround: int


def fleet_circulation(trips: tuple[Trip, ...], turnaround: int = 20) -> FleetPlan:
    """Resolve the fleet: matching-based itineraries with total deadhead.

    Chains are built deterministically: trip indices are scanned in order;
    each trip that is not the *successor* of an earlier trip starts a new
    trainset chain, which then follows the matching's successor links.
    """
    adjacency = compatibility_edges(trips, turnaround)
    matching = maximum_matching(adjacency)

    is_successor: set[int] = set(matching.values())
    chains: list[list[int]] = []
    used: set[int] = set()
    for left in range(len(trips)):
        if left in is_successor or left in used:
            continue
        chain: list[int] = [left]
        used.add(left)
        current = left
        while current in matching and matching[current] not in used:
            current = matching[current]
            chain.append(current)
            used.add(current)
        chains.append(chain)

    deadhead = 0
    for chain in chains:
        for prev, nxt in zip(chain, chain[1:]):
            deadhead += trips[nxt].depart - trips[prev].arrive
    return FleetPlan(
        trips=len(trips),
        trainsets=len(chains),
        matching_edges=len(matching),
        chains=tuple(tuple(trips[i].trip_id for i in chain) for chain in chains),
        deadhead_minutes=deadhead,
        turnaround=turnaround,
    )


def kuhn_munkres(cost: list[list[float]]) -> tuple[tuple[int, int, float], ...]:
    """Minimum-cost assignment (Hungarian algorithm) on a square cost matrix.

    Returns ``(row, column, cost)`` triples for the minimum total cost, in row
    order. The matrix must be square (pad with a large constant to add dummy
    rows/columns otherwise). Deterministic: row/column scans run in index
    order.
    """
    size = len(cost)
    if size == 0:
        return ()
    for cost_row in cost:
        if len(cost_row) != size:
            raise ValueError("cost matrix must be square")
        if any(not math.isfinite(value) for value in cost_row):
            raise ValueError("cost matrix entries must be finite")

    u = [0.0] * (size + 1)
    v = [0.0] * (size + 1)
    p = [0] * (size + 1)
    way = [0] * (size + 1)
    INF = float("inf")

    for worker in range(1, size + 1):
        p[0] = worker
        j0 = 0
        minv = [INF] * (size + 1)
        used = [False] * (size + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = 0
            for col in range(1, size + 1):
                if not used[col]:
                    current = cost[i0 - 1][col - 1] - u[i0] - v[col]
                    if current < minv[col]:
                        minv[col] = current
                        way[col] = j0
                    if minv[col] < delta:
                        delta = minv[col]
                        j1 = col
            for col in range(size + 1):
                if used[col]:
                    u[p[col]] += delta
                    v[col] -= delta
                else:
                    minv[col] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    assignment: list[tuple[int, int, float]] = []
    for col in range(1, size + 1):
        worker_idx = p[col] - 1
        assignment.append((worker_idx, col - 1, float(cost[worker_idx][col - 1])))
    assignment.sort(key=lambda entry: entry[0])
    return tuple(assignment)
