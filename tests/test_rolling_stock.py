"""Tests for :mod:`octopussy.rolling_stock` (trainset fleet circulation)."""

from __future__ import annotations

import pytest

from octopussy import rolling_stock as rs


def _trips():
    return (
        rs.Trip("T1", "dover", "calais", 60, 100),
        rs.Trip("T2", "calais", "amien", 120, 175),
        rs.Trip("T3", "amien", "paris", 195, 265),
        rs.Trip("T4", "paris", "garrison", 285, 335),
        rs.Trip("T5", "garrison", "monastery", 355, 400),
        rs.Trip("T6", "dover", "calais", 90, 130),
        rs.Trip("T7", "calais", "amien", 150, 205),
    )


def test_trip_validation():
    with pytest.raises(ValueError):
        rs.Trip("  ", "a", "b", 0, 5)
    with pytest.raises(ValueError):
        rs.Trip("T", "  ", "b", 0, 5)
    with pytest.raises(ValueError):
        rs.Trip("T", "a", " ", 0, 5)
    with pytest.raises(ValueError):
        rs.Trip("T", "a", "a", 0, 5)
    with pytest.raises(ValueError):
        rs.Trip("T", "a", "b", -1, 5)
    with pytest.raises(ValueError):
        rs.Trip("T", "a", "b", 10, 10)  # arrive not after depart


def test_can_follow():
    a = rs.Trip("A", "x", "y", 0, 10)
    b = rs.Trip("B", "y", "z", 30, 40)
    assert rs.can_follow(a, b, turnaround=20)
    late = rs.Trip("B", "y", "z", 25, 35)  # only 15 min after arrival
    assert not rs.can_follow(a, late, turnaround=20)
    other = rs.Trip("B", "w", "z", 30, 40)
    assert not rs.can_follow(a, other, turnaround=20)
    with pytest.raises(ValueError):
        rs.can_follow(a, b, turnaround=-1)


def test_compatibility_edges_shape():
    trips = _trips()
    edges = rs.compatibility_edges(trips, 20)
    assert len(edges) == 7
    # T1 (dover->calais, arrives 100) can be followed by any calais->* departure
    # at >= 120: T2 (120) and T7 (150).
    assert edges[0] == (1, 6)
    # T6 (dover->calais, arrives 130) can be followed by T7 (150).
    assert edges[5] == (6,)


def test_maximum_matching_size():
    trips = _trips()
    matching = rs.maximum_matching(rs.compatibility_edges(trips, 20))
    assert len(matching) == 5


def test_maximum_matching_empty():
    assert rs.maximum_matching(()) == {}
    assert rs.maximum_matching(((),)) == {}


def test_minimum_trainsets_known():
    assert rs.minimum_trainsets(_trips(), 20) == 2


def test_minimum_trainsets_single_trip():
    assert rs.minimum_trainsets((rs.Trip("A", "x", "y", 0, 10),), 20) == 1


def test_minimum_trainsets_incompatible():
    trips = (rs.Trip("A", "x", "y", 0, 10), rs.Trip("B", "y", "z", 5, 20))
    # B departs before A arrives -> the pair can never be chained.
    assert rs.minimum_trainsets(trips, 0) == 2
    assert rs.minimum_trainsets(trips, 20) == 2


def test_fleet_circulation_chains():
    plan = rs.fleet_circulation(_trips(), 20)
    assert plan.trips == 7
    assert plan.trainsets == 2
    assert plan.matching_edges == 5
    assert plan.deadhead_minutes == 100
    assert plan.chains == (("T1", "T2", "T3", "T4", "T5"), ("T6", "T7"))
    assert plan.turnaround == 20


def test_fleet_circulation_deterministic():
    a = rs.fleet_circulation(_trips(), 20)
    b = rs.fleet_circulation(_trips(), 20)
    assert a == b


def test_kuhn_munkres_empty():
    assert rs.kuhn_munkres([]) == ()


def test_kuhn_munkres_single():
    assignment = rs.kuhn_munkres([[5.0]])
    assert assignment == ((0, 0, 5.0),)


def test_kuhn_munkres_classic_optimum():
    cost = [[108.0, 125.0, 150.0], [150.0, 135.0, 175.0], [122.0, 148.0, 250.0]]
    assignment = rs.kuhn_munkres(cost)
    total = sum(c for _, _, c in assignment)
    assert total == pytest.approx(407.0)
    # row 0 -> col 2, row 1 -> col 1, row 2 -> col 0
    assert {r for r, _, _ in assignment} == {0, 1, 2}
    assert {c for _, c, _ in assignment} == {0, 1, 2}


def test_kuhn_munkres_deterministic_known():
    cost = [[10.0, 25.0, 15.0], [20.0, 12.0, 30.0], [18.0, 22.0, 16.0]]
    a1 = rs.kuhn_munkres(cost)
    a2 = rs.kuhn_munkres(cost)
    assert a1 == a2
    assert sum(c for _, _, c in a1) == pytest.approx(38.0)


def test_kuhn_munkres_validation():
    with pytest.raises(ValueError):
        rs.kuhn_munkres([[1.0, 2.0], [3.0]])  # non-square
    with pytest.raises(ValueError):
        rs.kuhn_munkres([[1.0, float("inf")], [3.0, 4.0]])
