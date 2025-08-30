from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

Material = Literal["brick", "stone", "hole", "filter", "gate"]


@dataclass
class Pixel:
    """Single map cell carrying material type and water depth."""

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
    rows: int
    cols: int
    grid: List[List[Pixel]] = field(default_factory=list)


def default_map(rows: int = 11, cols: int = 36) -> MapState:
    grid: List[List[Pixel]] = [
        [Pixel("hole", 0.0) for _ in range(cols)] for _ in range(rows)
    ]
    return MapState(rows, cols, grid)
