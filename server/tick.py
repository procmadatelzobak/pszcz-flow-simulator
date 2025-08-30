from __future__ import annotations

from .state import SimState

SOLID = {"brick", "stone"}
FILTER = {"filter"}


def _is_open(material: str) -> bool:
    return material not in SOLID


def flow_step(state: SimState) -> None:
    """Advance water simulation by one tick."""
    rows = len(state.grid)
    if rows == 0:
        return
    cols = len(state.grid[0])
    new_depths = [[cell.depth for cell in row] for row in state.grid]
    for r in range(rows - 1, -1, -1):
        for c in range(cols):
            cell = state.grid[r][c]
            if cell.material in SOLID:
                new_depths[r][c] = 0.0
                continue
            if cell.depth <= 0:
                continue
            below_r = r + 1
            if below_r < rows:
                below = state.grid[below_r][c]
                if _is_open(below.material):
                    transfer = cell.depth
                    if cell.material in FILTER:
                        transfer *= 0.5
                    new_depths[r][c] -= transfer
                    new_depths[below_r][c] += transfer
    for r in range(rows):
        for c in range(cols):
            state.grid[r][c].depth = max(new_depths[r][c], 0.0)
