from __future__ import annotations

from .state import SimState


SOLID = {"stone"}


def _is_open(material: str) -> bool:
    return material not in SOLID


def flow_step(state: SimState) -> None:
    """Advance water simulation by one tick."""

    rows = len(state.grid)
    if rows == 0:
        return
    cols = len(state.grid[0])

    # Springs produce water, sinks remove it before each step.
    for row in state.grid:
        for cell in row:
            if cell.material == "spring":
                cell.depth = 1.0
            elif cell.material == "sink":
                cell.depth = 0.0

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
                    new_depths[r][c] -= transfer
                    new_depths[below_r][c] += transfer

    for r in range(rows):
        for c in range(cols):
            cell = state.grid[r][c]
            cell.depth = max(min(new_depths[r][c], 1.0), 0.0)
            if cell.material == "spring":
                cell.depth = 1.0
            elif cell.material == "sink":
                cell.depth = 0.0

