from __future__ import annotations

from typing import TypedDict

from .model import FlowSnapshot, MapState


class MaterialSpec(TypedDict):
    emoji: str
    ascii: str
    color: str | None


MATERIALS: dict[str, MaterialSpec] = {
    "brick": {"emoji": "🧱", "ascii": "[]", "color": "31"},
    "stone": {"emoji": "🪨", "ascii": "##", "color": "37"},
    "hole": {"emoji": "  ", "ascii": "  ", "color": None},
    "filter": {"emoji": "🔳", "ascii": "FF", "color": "32"},
    "gate": {"emoji": "🚪", "ascii": "||", "color": "33"},
}

WATER_TILE = {"emoji": "💧", "ascii": "~~"}
WATER_COLORS = ["34", "36", "94", "96"]


def _bar(value: float, *, ascii: bool) -> str:
    filled = int(value * 4 + 0.5)
    if ascii:
        full, empty = "█", "░"
    else:
        full, empty = "▰", "▱"
    return full * filled + empty * (4 - filled)


def _color(text: str, code: str | None, *, no_ansi: bool) -> str:
    if no_ansi or not code:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def render(state: MapState, snap: FlowSnapshot, *, ascii: bool = False, no_ansi: bool = False) -> str:
    water_tile = WATER_TILE["ascii" if ascii else "emoji"]

    grid_lines: list[str] = []
    for row in state.grid:
        rendered: list[str] = []
        for cell in row:
            if cell.depth > 0:
                idx = min(int(cell.depth * len(WATER_COLORS)), len(WATER_COLORS) - 1)
                rendered.append(
                    _color(water_tile, WATER_COLORS[idx], no_ansi=no_ansi)
                )
            else:
                entry = MATERIALS.get(cell.material)
                if entry is None:
                    entry = {"emoji": "??", "ascii": "??", "color": None}
                ch = entry["ascii" if ascii else "emoji"]
                rendered.append(_color(ch, entry["color"], no_ansi=no_ansi))
        grid_lines.append("".join(rendered))

    alarm_line = ""
    if snap.alarm:
        alarm_line = ("! " if ascii else "⚠️ ") + snap.alarm

    status = (
        f"Source {_bar(snap.pressure_source, ascii=ascii)} ({snap.pressure_source:.2f}) | "
        f"Flow {_bar(snap.flow_rate, ascii=ascii)} ({snap.flow_rate:.2f}) | "
        f"Sink {_bar(snap.pressure_sink, ascii=ascii)} ({snap.pressure_sink:.2f})"
    )
    mode_line = f"Mode: {'ASCII' if ascii else 'Emoji'} | Res: {state.cm_per_pixel:.1f} cm/px"

    legend_items = []
    for name, entry in MATERIALS.items():
        ch = entry["ascii" if ascii else "emoji"]
        legend_items.append(f"{ch}={name}")
    water_levels = []
    for idx, code in enumerate(WATER_COLORS, 1):
        level = int(idx / len(WATER_COLORS) * 100)
        water_levels.append(
            f"{_color(water_tile, code, no_ansi=no_ansi)}{level}%"
        )
    legend_line = "Legend: " + ", ".join(legend_items) + " | Water: " + " ".join(water_levels)

    lines = [alarm_line] if alarm_line else []
    lines.extend(grid_lines)
    lines.append(status)
    lines.append(mode_line)
    lines.append(legend_line)
    frame = "\n".join(lines)
    if not no_ansi:
        frame = "\x1b[2J\x1b[H" + frame
    return frame
