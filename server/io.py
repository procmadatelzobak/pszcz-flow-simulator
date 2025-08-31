"""Input/output utilities for the server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .state import Pixel, SimState


def load_level(path: str | Path, sim: SimState) -> None:
    """Load a level file into ``sim``.

    The level schema is a JSON document containing only ``rows``, ``cols``,
    ``cm_per_pixel`` and a two-dimensional ``grid`` array. Each grid cell
    stores ``material`` and ``depth`` fields. Unknown fields are ignored to
    allow forward compatibility.
    """

    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    grid_data = data.get("grid") or data.get("pixels")
    if not isinstance(grid_data, list):
        grid_data = []
    sim.grid = [
        [
            Pixel(str(cell.get("material", "space")), float(cell.get("depth", 0.0)))
            for cell in row
        ]
        for row in grid_data
    ]


def save_level(
    path: str | Path,
    sim: SimState,
    *,
    cm_per_pixel: float = 1.0,
    meta: dict[str, Any] | None = None,
) -> None:
    """Export ``sim`` to ``path`` using the level JSON format."""

    rows = len(sim.grid)
    cols = len(sim.grid[0]) if rows else 0
    data: dict[str, Any] = {
        "rows": rows,
        "cols": cols,
        "cm_per_pixel": cm_per_pixel,
        "grid": [
            [{"material": cell.material, "depth": cell.depth} for cell in row]
            for row in sim.grid
        ],
    }
    if meta:
        data["meta"] = meta
    Path(path).write_text(json.dumps(data), encoding="utf-8")

