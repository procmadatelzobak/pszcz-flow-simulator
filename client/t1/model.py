"""Model objects shared by the :mod:`client.t1` renderer.

`MapState` holds a pixel grid. Each :class:`Pixel` stores the terrain
`material` and current water `depth` where ``0.0`` means dry and ``1.0``
represents a completely filled cell.
"""

from __future__ import annotations

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
    rows: int = 8, cols: int = 8, *, cm_per_pixel: float = 1.0
) -> MapState:
    """Create a simple map with a horizontal channel and boundary walls.

    The outer rim is filled with bricks while the middle row forms an open
    channel. The second cell of the channel contains water to act as the
    source. Other sizes fall back to the same pattern.
    """

    grid: List[List[Pixel]] = []
    for r in range(rows):
        row: List[Pixel] = []
        for c in range(cols):
            if r in (0, rows - 1) or c in (0, cols - 1):
                row.append(Pixel("brick", 0.0))
            else:
                row.append(Pixel("hole", 0.0))
        grid.append(row)

    if rows > 2 and cols > 2:
        mid = rows // 2
        for c in range(1, cols - 1):
            grid[mid][c] = Pixel("hole", 0.0)
        grid[mid][1].depth = 1.0  # source cell

    return MapState(rows, cols, grid, cm_per_pixel)
