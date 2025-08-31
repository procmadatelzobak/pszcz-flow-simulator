from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from server.io import load_level, save_level
from server.state import Pixel, SimState


def test_save_and_load_level(tmp_path: Path) -> None:
    sim = SimState()
    sim.grid = [
        [Pixel("space", 0.0), Pixel("stone", 0.0)],
        [Pixel("spring", 0.5), Pixel("sink", 0.0)],
    ]
    path = tmp_path / "level.json"
    save_level(path, sim, cm_per_pixel=1.0, meta={"note": "test"})

    data = json.loads(path.read_text())
    assert data["rows"] == 2
    assert data["cols"] == 2
    assert data["cm_per_pixel"] == 1.0
    assert data["grid"][1][0]["material"] == "spring"

    loaded = SimState()
    load_level(path, loaded)
    assert loaded.grid[1][0].material == "spring"
    assert loaded.grid[1][0].depth == 0.5
