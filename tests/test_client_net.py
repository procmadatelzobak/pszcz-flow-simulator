import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client import net


def test_build_hello(monkeypatch) -> None:
    monkeypatch.setattr(net.time, "time", lambda: 0)
    msg = net.build_hello("7")
    assert msg == {
        "t": "hello",
        "seq": "7",
        "ts": 0,
        "accept_major": [1],
        "min_minor": 0,
        "id_type": "string",
        "accept_features": [],
        "want_fields": ["node.p", "edge.q"],
        "client_version": "0.1.0",
    }

