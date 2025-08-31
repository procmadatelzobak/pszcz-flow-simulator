"""Client-side simulation state helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ClientState:
    """Minimal holder for the most recent grid snapshot.

    The interactive ``t0`` client keeps a copy of the server's grid so that
    commands such as ``set_depth`` can reuse the existing material when only the
    water level changes.
    """

    grid: List[List[Dict[str, Any]]] = field(default_factory=list)

    def update(self, snapshot: Dict[str, Any]) -> None:
        """Update state from a ``snapshot`` message."""

        grid = snapshot.get("grid", {}).get("cells", [])
        if isinstance(grid, list):
            self.grid = grid

    def material_at(self, r: int, c: int) -> str:
        """Return material at ``r``, ``c`` or ``space`` if unknown."""

        try:
            return self.grid[r][c]["material"]
        except Exception:  # pragma: no cover - out-of-bounds or malformed data
            return "space"

