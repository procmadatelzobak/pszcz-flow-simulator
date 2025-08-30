from __future__ import annotations

from .model import FlowSnapshot, MapState

MATERIAL_EMOJI = {
    "brick": "🧱",
    "stone": "🪨",
    "hole": "  ",
    "filter": "🔳",
    "gate": "🚪",
}
MATERIAL_ASCII = {
    "brick": "[]",
    "stone": "##",
    "hole": "  ",
    "filter": "FF",
    "gate": "||",
}


def _bar(value: float, *, ascii: bool) -> str:
    filled = int(value * 4 + 0.5)
    if ascii:
        full, empty = "█", "░"
    else:
        full, empty = "▰", "▱"
    return full * filled + empty * (4 - filled)


def render(state: MapState, snap: FlowSnapshot, *, ascii: bool = False, no_ansi: bool = False) -> str:
    palette = MATERIAL_ASCII if ascii else MATERIAL_EMOJI
    water_tile = "~~" if ascii else "💧"

    grid_lines: list[str] = []
    for row in state.grid:
        rendered: list[str] = []
        for cell in row:
            if cell.depth > 0:
                rendered.append(water_tile)
            else:
                rendered.append(palette.get(cell.material, "??"))
        grid_lines.append("".join(rendered))

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
