"""JSON import/export helpers for :class:`~client.t1.model.MapState`.

The file format stores `rows`, `cols`, global `cm_per_pixel` and a `grid`
array of pixels with `material` and `depth` fields.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import MapState, Pixel


def export_map(state: MapState) -> dict[str, Any]:
    return {
        "rows": state.rows,
        "cols": state.cols,
        "cm_per_pixel": state.cm_per_pixel,
        "grid": [
            [{"material": p.material, "depth": p.depth} for p in row]
            for row in state.grid
        ],
    }


def import_map(data: dict[str, Any]) -> MapState:
    rows = data["rows"]
    cols = data["cols"]
    cm_per_pixel = float(data.get("cm_per_pixel", 1.0))
    grid_data = data.get("grid", [])
    grid = [
        [Pixel(cell.get("material", "space"), float(cell.get("depth", 0.0))) for cell in row]
        for row in grid_data
    ]
    # Ensure grid has correct size
    if len(grid) < rows:
        grid.extend([[Pixel("space", 0.0) for _ in range(cols)] for _ in range(rows - len(grid))])
    for row in grid:
        if len(row) < cols:
            row.extend([Pixel("space", 0.0) for _ in range(cols - len(row))])
    return MapState(rows, cols, grid, cm_per_pixel)


def save_map(state: MapState, path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(export_map(state), f)


def load_map(path: str | Path) -> MapState:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return import_map(data)
