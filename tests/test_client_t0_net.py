import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client.t0.net import Seq, parse_command
from client.t0.state import ClientState


def test_parse_set_pixel() -> None:
    seq = Seq()
    state = ClientState()
    msg = parse_command("set_pixel 1 2 stone 0.5", seq, state)
    assert msg is not None
    assert msg["t"] == "edit_grid"
    assert msg["ops"] == [
        {"op": "set_pixel", "r": 1, "c": 2, "material": "stone", "depth": 0.5}
    ]


def test_parse_set_depth_uses_state() -> None:
    seq = Seq()
    state = ClientState()
    state.update({"grid": {"cells": [[{"material": "spring", "depth": 0.0}]]}})
    msg = parse_command("set_depth 0 0 0.3", seq, state)
    assert msg is not None
    assert msg["ops"] == [
        {"op": "set_pixel", "r": 0, "c": 0, "material": "spring", "depth": 0.3}
    ]

