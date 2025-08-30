"""Input/output utilities for the server."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from .state import SimState


def load_level(path: str | Path, sim: SimState) -> None:
    """Load a level file into ``sim``.

    The level schema is a JSON document containing ``nodes`` and ``pipes``
    arrays. All extra fields on nodes and pipes are stored inside the
    ``params`` mapping of :class:`SimState` entries so the simulation can
    evolve without a fixed schema.
    """
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    sim.nodes = {}
    sim.pipes = {}
    for node in data.get("nodes", []):
        params = {k: v for k, v in node.items() if k not in {"id", "type"}}
        sim.nodes[node["id"]] = {
            "id": node["id"],
            "type": node.get("type", "junction"),
            "params": params,
            "state": {"p": 0},
        }
    for pipe in data.get("pipes", []):
        params = {k: v for k, v in pipe.items() if k not in {"id", "a", "b"}}
        sim.pipes[pipe["id"]] = {
            "id": pipe["id"],
            "a": pipe["a"],
            "b": pipe["b"],
            "params": params,
            "state": {"q": 0, "dir": 0},
        }
