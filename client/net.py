"""Thin wrapper exposing the interactive t0 client as ``client.net``.

The underlying client already supports a ``--url`` flag to target a custom
WebSocket endpoint.
"""

from __future__ import annotations

from client.t0 import net as _t0_net

build_hello = _t0_net.build_hello


def main() -> None:
    _t0_net.main()


if __name__ == "__main__":
    main()
