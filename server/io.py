"""Input/output utilities for the server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .state import Pixel, SimState


def load_level(path: str | Path, sim: SimState) -> None:
    """Load a level file into ``sim``.

    The level schema is a JSON document containing a ``grid`` object with a
    ``cells`` array describing the pixel materials and water depths. Unknown
    fields are ignored to allow forward compatibility.
    """

    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    grid = data.get("grid")
    if isinstance(grid, dict):
        cells = grid.get("cells")
    else:
        cells = grid
    sim.grid = [
        [
            Pixel(str(cell.get("material", "space")), float(cell.get("depth", 0.0)))
            for cell in row
        ]
        for row in cells or []
    ]

