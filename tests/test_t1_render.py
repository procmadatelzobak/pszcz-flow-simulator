import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client.t1 import adapter, model, view


SEED = 123
BASE = adapter.MockAdapter(seed=SEED).snapshot().pressure_source
SINK = BASE * 0.8


def _expected(flow: float, pipe: str, *, ascii: bool = False) -> str:
    rows, cols = 11, 36
    mid = rows // 2
    empty = ("  " if ascii else " ") * cols
    grid = [empty for _ in range(mid)]
    if ascii:
        row = "  " * 2 + "P " + pipe * 31 + "S " + "  "
    else:
        row = "  🚰" + pipe * 31 + "🕳️ "
    grid.append(row)
    grid.extend([empty for _ in range(rows - mid - 1)])
    def bar(v: float, full: str, empty: str) -> str:
        filled = int(v * 4 + 0.5)
        return full * filled + empty * (4 - filled)
    if ascii:
        src_bar = bar(BASE, "█", "░")
        flow_bar = bar(flow, "█", "░")
        sink_bar = bar(SINK, "█", "░")
    else:
        src_bar = bar(BASE, "▰", "▱")
        flow_bar = bar(flow, "▰", "▱")
        sink_bar = bar(SINK, "▰", "▱")
    status = f"Source {src_bar} ({BASE:.2f}) | Flow {flow_bar} ({flow:.2f}) | Sink {sink_bar} ({SINK:.2f})"
    grid.append(status)
    return "\n".join(grid)


def test_render_emoji_low() -> None:
    state = model.default_map()
    snap = adapter.MockAdapter(seed=SEED, rate=0.25).snapshot()
    frame = view.render(state, snap, no_ansi=True)
    assert frame == _expected(0.25, "💧")


def test_render_emoji_high() -> None:
    state = model.default_map()
    snap = adapter.MockAdapter(seed=SEED, rate=0.75).snapshot()
    frame = view.render(state, snap, no_ansi=True)
    assert frame == _expected(0.75, "🌊")


def test_render_ascii() -> None:
    state = model.default_map()
    snap = adapter.MockAdapter(seed=SEED, rate=0.25).snapshot()
    frame = view.render(state, snap, ascii=True, no_ansi=True)
    assert frame == _expected(0.25, "--", ascii=True)
