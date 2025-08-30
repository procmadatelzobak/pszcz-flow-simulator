"""In-memory simulation state and grid edit application logic.

The simulator maintains a rectangular pixel grid. Each cell stores a terrain
``material`` and water ``depth`` in the ``0.0–1.0`` range.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Supported materials for a :class:`Pixel`.
VALID_MATERIALS = {"stone", "space", "spring", "sink"}

# Classification of materials used by the simulation.
SOLID_MATERIALS = {"stone"}
PASSABLE_MATERIALS = {"space", "spring", "sink"}


@dataclass
class Pixel:
    """Single cell in the simulation grid.

    Attributes
    ----------
    material:
        One of ``stone``, ``space``, ``spring`` or ``sink``.
    depth:
        Fraction ``0.0–1.0`` describing how full the cell is with water.
    """

    material: str
    depth: float = 0.0


@dataclass
class SimState:
    """Simulation state consisting only of the pixel grid."""

    grid: List[List[Pixel]] = field(default_factory=list)

    def snapshot(self) -> Dict[str, Any]:
        """Return a snapshot of the current grid."""

        return {
            "grid": [
                [
                    {"material": cell.material, "depth": cell.depth}
                    for cell in row
                ]
                for row in self.grid
            ]
        }

    def apply_edits(self, edits: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """Apply a batch of grid edits atomically.

        Supported operations
        --------------------
        ``set_pixel``
            ``{"op":"set_pixel","r":int,"c":int,"material":str,"depth":float?}``
        ``fill``
            ``{"op":"fill","r":int,"c":int}`` – set depth to ``1.0``.
        ``drain``
            ``{"op":"drain","r":int,"c":int}`` – set depth to ``0.0``.

        Returns ``None`` on success or an error ``{"code": str}`` mapping on
        failure.
        """

        rows = len(self.grid)
        cols = len(self.grid[0]) if rows else 0

        for edit in edits:
            op = edit.get("op")
            r = edit.get("r")
            c = edit.get("c")
            if not isinstance(r, int) or not isinstance(c, int):
                return {"code": "bad_request"}
            if r < 0 or c < 0 or r >= rows or c >= cols:
                return {"code": "index_out_of_bounds"}
            cell = self.grid[r][c]

            if op == "set_pixel":
                material = edit.get("material")
                if material not in VALID_MATERIALS:
                    return {"code": "invalid_material"}
                cell.material = material
                depth = edit.get("depth")
                if depth is not None:
                    try:
                        cell.depth = max(0.0, min(1.0, float(depth)))
                    except (TypeError, ValueError):
                        return {"code": "bad_request"}
            elif op == "fill":
                cell.depth = 1.0
            elif op == "drain":
                cell.depth = 0.0
            else:
                return {"code": "bad_request"}

        return None

