import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from client.t1 import adapter


def test_mock_deterministic() -> None:
    a1 = adapter.MockAdapter(seed=1, rate=0.3)
    a2 = adapter.MockAdapter(seed=1, rate=0.3)
    assert a1.snapshot() == a2.snapshot()


def test_socket_fallback() -> None:
    mock = adapter.MockAdapter(seed=2, rate=0.4)
    sock = adapter.SocketAdapter("ws://example", mock)
    snap = sock.snapshot()
    assert snap.alarm is not None
    expected = adapter.MockAdapter(seed=2, rate=0.4).snapshot()
    assert (
        snap.pressure_source,
        snap.flow_rate,
        snap.pressure_sink,
    ) == (
        expected.pressure_source,
        expected.flow_rate,
        expected.pressure_sink,
    )
