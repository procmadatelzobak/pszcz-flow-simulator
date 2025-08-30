from __future__ import annotations

import json
from pathlib import Path

from .model import MapState, Pump, Pipe, Sink


def export_map(state: MapState) -> dict:
    return {
        "rows": state.rows,
        "cols": state.cols,
        "pump": {"row": state.pump.row, "col": state.pump.col},
        "pipe": {
            "row": state.pipe.row,
            "start_col": state.pipe.start_col,
            "end_col": state.pipe.end_col,
        },
        "sink": {"row": state.sink.row, "col": state.sink.col},
    }


def import_map(data: dict) -> MapState:
    return MapState(
        rows=data["rows"],
        cols=data["cols"],
        pump=Pump(**data["pump"]),
        pipe=Pipe(**data["pipe"]),
        sink=Sink(**data["sink"]),
    )


def save_map(state: MapState, path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(export_map(state), f)


def load_map(path: str | Path) -> MapState:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return import_map(data)
