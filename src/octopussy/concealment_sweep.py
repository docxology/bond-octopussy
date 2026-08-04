"""Concealed-device detection sweep: radiation + shape/mass anomaly.

A concealed nuclear device hides in plain sight: small, dense, and warm. This
module runs a two-channel sweep over the target area:

1. **Radiation anomaly** — a grid of scintillation detectors records gamma
   count rates. A source adds an inverse-square count rate on top of a
   Poisson background; the sweep estimates background by median filtering and
   flags statistically-significant hot spots (z-scores), then locates peaks.

2. **Shape/mass anomaly** — cargo manifests give each item a volume and a
   mass. Against per-category expected densities, an item that is far heavier
   than its volume allows (a dense core hidden inside a small shell — the
   Fabergé-egg signature) scores a large mass anomaly.

:func:`fuse_concealment_report` merges both channels into one prioritized
sweep report. All randomness is confined to seeded Poisson draws of the
detector model; detection itself is deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "CATALOG_CATEGORIES",
    "CATALOG_SIZE",
    "Container",
    "ConcealmentEntry",
    "ConcealmentReport",
    "Hotspot",
    "MassAnomaly",
    "RadiationSource",
    "SweepGrid",
    "estimate_background",
    "anomaly_map",
    "detect_hotspots",
    "fuse_concealment_report",
    "mass_anomaly",
    "simulate_sweep",
]


@dataclass(frozen=True)
class RadiationSource:
    """A gamma emitter at a planar position with an intensity."""

    position: tuple[float, float]
    intensity: float  # counts/s at unit distance (before background)


@dataclass(frozen=True)
class SweepGrid:
    """A rectangular detector lattice over the target area."""

    origin: tuple[float, float]  # (x, y) of the south-west corner
    spacing: float
    nx: int
    ny: int
    standoff: float = 1.0  # detector elevation above the plane (m)

    def __post_init__(self) -> None:
        if self.spacing <= 0.0:
            raise ValueError("spacing must be positive")
        if self.nx <= 0 or self.ny <= 0:
            raise ValueError("grid dimensions must be positive")
        if self.standoff <= 0.0:
            raise ValueError("standoff must be positive")

    def detector_positions(self) -> np.ndarray:
        """Return an (nx*ny, 2) array of detector (x, y) positions."""
        xs = self.origin[0] + self.spacing * np.arange(self.nx, dtype=float)
        ys = self.origin[1] + self.spacing * np.arange(self.ny, dtype=float)
        grid_x, grid_y = np.meshgrid(xs, ys, indexing="ij")
        return np.asarray(np.column_stack([grid_x.ravel(), grid_y.ravel()]), dtype=float)


@dataclass(frozen=True)
class Hotspot:
    """A detected radiation peak."""

    position: tuple[float, float]
    score: float  # z-score above background


@dataclass(frozen=True)
class Container:
    """A cargo item with its manifest volume, mass, and category."""

    name: str
    volume_m3: float
    mass_kg: float
    category: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Container.name must be non-empty")
        if self.volume_m3 <= 0.0:
            raise ValueError("Container.volume_m3 must be positive")
        if self.mass_kg < 0.0:
            raise ValueError("Container.mass_kg must be non-negative")


@dataclass(frozen=True)
class MassAnomaly:
    """The result of screening one container's shape/mass profile."""

    name: str
    category: str
    volume_m3: float
    mass_kg: float
    expected_mass_kg: float
    density_ratio: float  # measured density / category expected density
    mass_z: float  # how many tolerances above the expected mass


@dataclass(frozen=True)
class ConcealmentEntry:
    """A single ranked suspicion in the fused sweep report."""

    kind: str  # "radiation" | "mass"
    name: str
    score: float
    detail: str


@dataclass
class ConcealmentReport:
    """Prioritized merged sweep report."""

    entries: tuple[ConcealmentEntry, ...]  # sorted by score, descending
    flagged: tuple[str, ...]  # names above the confirmation threshold
    worst: ConcealmentEntry | None


def _build_catalog() -> dict[str, tuple[float, float, float]]:
    """Category → (expected density kg/m3, density sigma kg/m3, mass tolerance).

    Deterministic physical-profile table used to judge whether an item's mass
    is credible for its volume.
    """
    return {
        "crate": (180.0, 40.0, 0.25),
        "typewriter": (220.0, 50.0, 0.20),
        "luggage": (160.0, 35.0, 0.25),
        "egg": (1200.0, 300.0, 0.30),
        "sculpture": (2600.0, 400.0, 0.20),
        "trapdoor": (850.0, 150.0, 0.25),
    }


#: Deterministic per-category physical profile table.
_catalog: dict[str, tuple[float, float, float]] = _build_catalog()
CATALOG_CATEGORIES: tuple[str, ...] = tuple(sorted(_catalog))
CATALOG_SIZE: int = len(_catalog)


def simulate_sweep(
    grid: SweepGrid,
    background_cps: float,
    sources: tuple[RadiationSource, ...],
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Record detector count rates across the grid.

    Each detector sees ``background + sum(intensity / (r^2 + standoff^2))``
    and draws one Poisson sample. Returns ``(positions, counts)`` where
    ``counts`` is an (nx, ny) array aligned with the lattice.
    """
    if background_cps < 0.0:
        raise ValueError("background_cps must be non-negative")
    positions = grid.detector_positions()
    expected = np.full(positions.shape[0], background_cps, dtype=float)
    for source in sources:
        dx = positions[:, 0] - source.position[0]
        dy = positions[:, 1] - source.position[1]
        radius_sq = dx * dx + dy * dy + grid.standoff * grid.standoff
        expected += source.intensity / np.maximum(radius_sq, 1e-6)
    rng = np.random.default_rng(seed)
    counts = rng.poisson(expected).reshape(grid.nx, grid.ny).astype(float)
    return positions, counts


def _windowed_median(grid: np.ndarray, radius: int = 1) -> np.ndarray:
    """Return a median-filtered copy of ``grid`` (square window, no padding)."""
    nx, ny = grid.shape
    out = np.zeros_like(grid)
    for i in range(nx):
        i0, i1 = max(0, i - radius), min(nx, i + radius + 1)
        for j in range(ny):
            j0, j1 = max(0, j - radius), min(ny, j + radius + 1)
            out[i, j] = float(np.median(grid[i0:i1, j0:j1]))
    return out


def estimate_background(counts: np.ndarray, radius: int = 1) -> np.ndarray:
    """Median-filtered background estimate for a count map."""
    if counts.ndim != 2 or counts.shape[0] == 0 or counts.shape[1] == 0:
        raise ValueError("counts must be a non-empty 2D array")
    return _windowed_median(np.asarray(counts, dtype=float), radius)


def anomaly_map(counts: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Poisson-normalized z-score map: (counts - bg) / sqrt(max(bg, 1))."""
    counts = np.asarray(counts, dtype=float)
    background = np.asarray(background, dtype=float)
    denominator = np.sqrt(np.maximum(background, 1.0))
    return np.asarray((counts - background) / denominator, dtype=float)


def detect_hotspots(
    counts: np.ndarray,
    anomaly: np.ndarray,
    threshold: float,
    *,
    min_score: float = 0.0,
) -> tuple[Hotspot, ...]:
    """Locate local-maximum hotspots whose z-score clears ``threshold``.

    Returns peaks in deterministic (row, column) order. A cell is a hotspot
    when its anomaly score is ``>=`` every neighbour's score and equals or
    exceeds the given threshold.
    """
    counts = np.asarray(counts, dtype=float)
    anomaly = np.asarray(anomaly, dtype=float)
    nx, ny = counts.shape
    found: list[Hotspot] = []
    for i in range(nx):
        for j in range(ny):
            score = float(anomaly[i, j])
            if score < threshold or score < min_score:
                continue
            value = float(counts[i, j])
            neighbours = _neighbour_values(counts, i, j, nx, ny)
            if all(value >= nv for nv in neighbours):
                found.append(Hotspot((float(i), float(j)), score))
    return tuple(found)


def _neighbour_values(grid: np.ndarray, i: int, j: int, nx: int, ny: int) -> list[float]:
    """Values of the 8-connected neighbours of cell (i, j) inside the grid."""
    values: list[float] = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if 0 <= ni < nx and 0 <= nj < ny:
                values.append(float(grid[ni, nj]))
    return values


def mass_anomaly(container: Container, catalog: dict[str, tuple[float, float, float]] | None = None) -> MassAnomaly:
    """Compute the shape/mass anomaly of one container against the catalog."""
    table = _catalog if catalog is None else catalog
    if container.category not in table:
        raise KeyError(f"no physical profile for category {container.category!r}")
    density, sigma, tolerance = table[container.category]
    expected_mass = density * container.volume_m3
    density_ratio = container.mass_kg / container.volume_m3 / density if container.volume_m3 else 0.0
    mass_z = (container.mass_kg - expected_mass) / (tolerance * expected_mass + 1e-9)
    return MassAnomaly(
        name=container.name,
        category=container.category,
        volume_m3=container.volume_m3,
        mass_kg=container.mass_kg,
        expected_mass_kg=expected_mass,
        density_ratio=density_ratio,
        mass_z=mass_z,
    )


def fuse_concealment_report(
    radiation_hits: tuple[Hotspot, ...],
    containers: tuple[Container, ...],
    catalog: dict[str, tuple[float, float, float]] | None = None,
    *,
    mass_z_threshold: float = 2.0,
    radiation_threshold: float = 3.0,
) -> ConcealmentReport:
    """Merge radiation hotspots and mass anomalies into one prioritized report."""
    entries: list[ConcealmentEntry] = []
    for hit in radiation_hits:
        entries.append(
            ConcealmentEntry(
                kind="radiation",
                name=f"hotspot@{hit.position[0]:.0f},{hit.position[1]:.0f}",
                score=hit.score,
                detail=f"radiation z={hit.score:.2f}",
            )
        )
    for container in containers:
        anomaly = mass_anomaly(container, catalog)
        if anomaly.mass_z >= mass_z_threshold:
            entries.append(
                ConcealmentEntry(
                    kind="mass",
                    name=container.name,
                    score=anomaly.mass_z,
                    detail=f"mass {anomaly.mass_z:.2f}x tolerance, density ratio {anomaly.density_ratio:.2f}",
                )
            )
    entries.sort(key=lambda e: (-e.score, e.kind, e.name))
    flagged = tuple(
        e.name for e in entries if e.score >= (radiation_threshold if e.kind == "radiation" else mass_z_threshold)
    )
    worst = entries[0] if entries else None
    return ConcealmentReport(tuple(entries), flagged, worst)


#: Deterministic canonical scenario: a concealed source under a dense "egg".
DEFAULT_CONTAINERS: tuple[Container, ...] = (
    Container("cash_crate", 0.40, 78.0, "crate"),
    Container("royal_egg", 0.002, 7.5, "egg"),
    Container("typewriter", 0.06, 6.5, "typewriter"),
    Container("luggage_case", 0.09, 15.0, "luggage"),
)
