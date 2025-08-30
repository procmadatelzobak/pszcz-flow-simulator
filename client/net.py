"""Minimal client helpers for protocol handshakes."""

from __future__ import annotations

import time
from typing import Any, Dict

from client.t0 import net as _t0_net


def build_hello(seq: str = "1") -> Dict[str, Any]:
    """Return a hello message following :mod:`PROTOCOL`."""

    return {
        "t": "hello",
        "seq": seq,
        "ts": int(time.time() * 1000),
        "accept_major": [2],
        "min_minor": 0,
        "client_version": "0.2.0",
    }


def main() -> None:  # pragma: no cover - thin wrapper
    _t0_net.main()


if __name__ == "__main__":  # pragma: no cover
    main()

