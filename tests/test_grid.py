from __future__ import annotations

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client.t1.model import default_map
from client.t1.serialize import export_map, import_map
from server.state import Pixel as SPixel, SimState
from server.tick import flow_step


def test_map_serialization_roundtrip() -> None:
    state = default_map(2, 2)
    state.grid[0][0].material = "hole"
    state.grid[0][0].depth = 1.0
    data = export_map(state)
    loaded = import_map(data)
    assert loaded.grid[0][0].material == "hole"
    assert loaded.grid[0][0].depth == 1.0


def test_water_flows_down() -> None:
    sim = SimState()
    sim.grid = [[SPixel("hole", 1.0)], [SPixel("hole", 0.0)]]
    flow_step(sim)
    assert sim.grid[0][0].depth == 0.0
    assert sim.grid[1][0].depth == 1.0


def test_filter_reduces_flow() -> None:
    sim = SimState()
    sim.grid = [[SPixel("filter", 1.0)], [SPixel("hole", 0.0)]]
    flow_step(sim)
    assert sim.grid[0][0].depth == 0.5
    assert sim.grid[1][0].depth == 0.5
