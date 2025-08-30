from __future__ import annotations

from .model import FlowSnapshot, MapState


def _pipe_char(flow: float, ascii: bool) -> str:
    if ascii:
        return "==" if flow >= 0.5 else "--"
    if flow < 0.2:
        return "▫️"
    if flow < 0.6:
        return "💧"
    return "🌊"


def _bar(value: float, *, ascii: bool) -> str:
    filled = int(value * 4 + 0.5)
    if ascii:
        full, empty = "█", "░"
    else:
        full, empty = "▰", "▱"
    return full * filled + empty * (4 - filled)


def render(state: MapState, snap: FlowSnapshot, *, ascii: bool = False, no_ansi: bool = False) -> str:
    pump_tile = "P " if ascii else "🚰"
    sink_tile = "S " if ascii else "🕳️"
    empty_tile = "  " if ascii else " "
    pipe_tile = _pipe_char(snap.flow_rate, ascii)

    grid_lines: list[str] = []
    for r in range(state.rows):
        row: list[str] = []
        for c in range(state.cols):
            if r == state.pump.row and c == state.pump.col:
                row.append(pump_tile)
            elif r == state.sink.row and c == state.sink.col:
                row.append(sink_tile)
            elif r == state.pipe.row and state.pipe.start_col <= c <= state.pipe.end_col:
                row.append(pipe_tile)
            else:
                row.append(empty_tile)
        grid_lines.append("".join(row))

    alarm_line = ""
    if snap.alarm:
        alarm_line = ("! " if ascii else "⚠️ ") + snap.alarm

    status = (
        f"Source {_bar(snap.pressure_source, ascii=ascii)} ({snap.pressure_source:.2f}) | "
        f"Flow {_bar(snap.flow_rate, ascii=ascii)} ({snap.flow_rate:.2f}) | "
        f"Sink {_bar(snap.pressure_sink, ascii=ascii)} ({snap.pressure_sink:.2f})"
    )

    lines = [alarm_line] if alarm_line else []
    lines.extend(grid_lines)
    lines.append(status)
    frame = "\n".join(lines)
    if not no_ansi:
        frame = "\x1b[2J\x1b[H" + frame
    return frame
