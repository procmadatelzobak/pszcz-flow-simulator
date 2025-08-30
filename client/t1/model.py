from __future__ import annotations

"""Model objects shared by the :mod:`client.t1` renderer.

`MapState` holds a pixel grid. Each :class:`Pixel` stores the terrain
`material` and current water `depth` where ``0.0`` means dry and ``1.0``
represents a completely filled cell.
"""

from dataclasses import dataclass, field
from typing import List, Literal

Material = Literal["brick", "stone", "hole", "filter", "gate"]


@dataclass
class Pixel:
    """Single map cell carrying material type and water depth.

    Parameters
    ----------
    material:
        One of ``"brick"``, ``"stone"``, ``"hole"``, ``"filter"`` or ``"gate"``.
    depth:
        Fraction ``0.0–1.0`` describing how full the cell is with water.
    """

    material: Material
    depth: float = 0.0


@dataclass
class FlowSnapshot:
    pressure_source: float
    flow_rate: float
    pressure_sink: float
    alarm: str | None = None


@dataclass
class MapState:
    """Grid dimensions and pixel data for the simulation map."""

    rows: int
    cols: int
    grid: List[List[Pixel]] = field(default_factory=list)
    cm_per_pixel: float = 1.0


def default_map(
    rows: int = 11, cols: int = 36, *, cm_per_pixel: float = 1.0
) -> MapState:
    grid: List[List[Pixel]] = [
        [Pixel("hole", 0.0) for _ in range(cols)] for _ in range(rows)
    ]
    return MapState(rows, cols, grid, cm_per_pixel)
