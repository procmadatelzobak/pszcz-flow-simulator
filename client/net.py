"""Minimal console client networking."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict

import websockets  # type: ignore[import-not-found]


logger = logging.getLogger(__name__)


def build_hello(seq: str = "1") -> Dict[str, Any]:
    """Return a hello message following :mod:`PROTOCOL`.

    Parameters
    ----------
    seq:
        Sequence identifier for the message.
    """

    return {
        "t": "hello",
        "seq": seq,
        "ts": int(time.time() * 1000),
        "accept_major": [1],
        "min_minor": 0,
        "id_type": "string",
        "accept_features": [],
        "want_fields": ["node.p", "edge.q"],
        "client_version": "0.1.0",
    }


async def main() -> None:
    """Connect to the server and print snapshot information."""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    uri = "ws://127.0.0.1:7777/ws"
    hello = build_hello()
    async with websockets.connect(uri) as ws:  # type: ignore[arg-type]
        await ws.send(json.dumps(hello))
        welcome = json.loads(await ws.recv())
        print(welcome)

        start = time.monotonic()
        count = 0
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:  # pragma: no cover - ignore bad messages
                continue
            if msg.get("t") != "snapshot":
                continue
            count += 1
            elapsed = time.monotonic() - start
            rate = count / elapsed if elapsed else 0.0
            tick = msg.get("tick")
            print(f"tick={tick} rate={rate:.1f} msg/s")


if __name__ == "__main__":
    asyncio.run(main())

