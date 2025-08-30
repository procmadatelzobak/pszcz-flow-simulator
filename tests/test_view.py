from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client.t1.model import FlowSnapshot, MapState, Pixel
from client.t1.view import render


def _sample_state() -> MapState:
    return MapState(
        2,
        2,
        [
            [Pixel("brick", 0.0), Pixel("hole", 0.5)],
            [Pixel("filter", 0.0), Pixel("stone", 0.0)],
        ],
        1.0,
    )


def _sample_snap() -> FlowSnapshot:
    return FlowSnapshot(0.0, 0.0, 0.0)


def test_render_no_ansi_snapshot() -> None:
    state = _sample_state()
    snap = _sample_snap()
    frame = render(state, snap, ascii=False, no_ansi=True)
    expected = (
        "🧱💧\n"
        "🔳🪨\n"
        "Source ▱▱▱▱ (0.00) | Flow ▱▱▱▱ (0.00) | Sink ▱▱▱▱ (0.00)\n"
        "Mode: Emoji | Res: 1.0 cm/px\n"
        "Legend: 🧱=brick, 🪨=stone,   =hole, 🔳=filter, 🚪=gate | Water: 💧25% 💧50% 💧75% 💧100%"
    )
    assert frame == expected
    assert "\x1b" not in frame


def test_render_ascii_fallback_snapshot() -> None:
    state = _sample_state()
    snap = _sample_snap()
    frame = render(state, snap, ascii=True, no_ansi=True)
    expected = (
        "[]~~\n"
        "FF##\n"
        "Source ░░░░ (0.00) | Flow ░░░░ (0.00) | Sink ░░░░ (0.00)\n"
        "Mode: ASCII | Res: 1.0 cm/px\n"
        "Legend: []=brick, ##=stone,   =hole, FF=filter, ||=gate | Water: ~~25% ~~50% ~~75% ~~100%"
    )
    assert frame == expected
    assert "\x1b" not in frame

