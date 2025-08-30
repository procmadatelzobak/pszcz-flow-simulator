from __future__ import annotations

import random
from dataclasses import replace

from .model import FlowSnapshot


class MockAdapter:
    """Deterministic mock data source."""

    def __init__(self, *, seed: int | None = None, rate: float = 0.5) -> None:
        self._rng = random.Random(seed)
        self.rate = rate

    def snapshot(self) -> FlowSnapshot:
        base = self._rng.random()
        return FlowSnapshot(
            pressure_source=base,
            flow_rate=self.rate,
            pressure_sink=base * 0.8,
        )


class SocketAdapter:
    """Scaffold that falls back to :class:`MockAdapter`."""

    def __init__(self, endpoint: str, mock: MockAdapter) -> None:
        self.endpoint = endpoint
        self.mock = mock
        self.alarm: str | None = None
        self.connected = False

    def snapshot(self) -> FlowSnapshot:
        if not self.connected:
            self.alarm = "no server connection — running MOCK"
            snap = self.mock.snapshot()
            return replace(snap, alarm=self.alarm)
        return self.mock.snapshot()
