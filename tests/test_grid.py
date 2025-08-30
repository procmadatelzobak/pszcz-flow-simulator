from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client.t1.model import default_map
from client.t1.serialize import export_map, import_map
from server.state import Pixel as SPixel, SimState
from server.tick import flow_step


def test_map_serialization_roundtrip() -> None:
    state = default_map(2, 2, cm_per_pixel=1.0)
    state.grid[0][0].material = "space"
    state.grid[0][0].depth = 1.0
    data = export_map(state)
    loaded = import_map(data)
    assert loaded.grid[0][0].material == "space"
    assert loaded.grid[0][0].depth == 1.0
    assert data["cm_per_pixel"] == 1.0
    assert loaded.cm_per_pixel == 1.0


def test_water_flows_down() -> None:
    sim = SimState()
    sim.grid = [[SPixel("space", 1.0)], [SPixel("space", 0.0)]]
    flow_step(sim)
    assert sim.grid[0][0].depth == 0.0
    assert sim.grid[1][0].depth == 1.0


def test_spring_and_sink_behaviour() -> None:
    sim = SimState()
    sim.grid = [[SPixel("spring", 0.0)], [SPixel("sink", 0.5)]]
    flow_step(sim)
    assert sim.grid[0][0].depth == 0.0  # spring empties after emission
    assert sim.grid[1][0].depth == 0.0  # sink removes incoming water


def test_spring_emits_water() -> None:
    sim = SimState()
    sim.grid = [[SPixel("spring", 0.0)], [SPixel("space", 0.0)]]
    flow_step(sim)
    assert sim.grid[0][0].depth == 0.0
    assert sim.grid[1][0].depth == 1.0

