from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Pump:
    row: int
    col: int


@dataclass
class Pipe:
    row: int
    start_col: int
    end_col: int


@dataclass
class Sink:
    row: int
    col: int


@dataclass
class FlowSnapshot:
    pressure_source: float
    flow_rate: float
    pressure_sink: float
    alarm: str | None = None


@dataclass
class MapState:
    rows: int
    cols: int
    pump: Pump
    pipe: Pipe
    sink: Sink


def default_map(rows: int = 11, cols: int = 36) -> MapState:
    mid = rows // 2
    pump = Pump(mid, 2)
    pipe = Pipe(mid, 3, cols - 3)
    sink = Sink(mid, cols - 2)
    return MapState(rows, cols, pump, pipe, sink)
