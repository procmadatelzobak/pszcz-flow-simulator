import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client import net


def _seq() -> net.Seq:
    return net.Seq()


def test_parse_add_node(monkeypatch) -> None:
    monkeypatch.setattr(net, "_now_ms", lambda: 0)
    msg = net.parse_command("add_node n1 source", _seq())
    assert msg == {
        "t": "edit_batch",
        "seq": "1",
        "ts": 0,
        "edits": [
            {"op": "add_node", "id": "n1", "type": "source", "params": {}}
        ],
    }


def test_parse_set_param(monkeypatch) -> None:
    monkeypatch.setattr(net, "_now_ms", lambda: 0)
    msg = net.parse_command("set_param n1 target_pressure 101", _seq())
    assert msg and msg["edits"][0]["value"] == 101
    msg2 = net.parse_command("set_param n1 label hello", _seq())
    assert msg2 and msg2["edits"][0]["value"] == "hello"


def test_parse_control(monkeypatch) -> None:
    monkeypatch.setattr(net, "_now_ms", lambda: 0)
    seq = _seq()
    assert net.parse_command("pause", seq) == {
        "t": "control",
        "seq": "1",
        "ts": 0,
        "pause": True,
    }
    rate_msg = net.parse_command("rate 40", seq)
    assert rate_msg and rate_msg["tick_hz"] == 40


def test_parse_save(monkeypatch) -> None:
    monkeypatch.setattr(net, "_now_ms", lambda: 0)
    msg = net.parse_command("save", _seq())
    assert msg == {"t": "save", "seq": "1", "ts": 0}


def test_parse_invalid() -> None:
    assert net.parse_command("bogus", _seq()) is None

