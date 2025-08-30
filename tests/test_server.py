import asyncio
import contextlib
import json
import sys
from pathlib import Path

import websockets  # type: ignore[import-not-found]

# Ensure repository root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from server import net


HELLO = {
    "t": "hello",
    "seq": "1",
    "ts": 0,
    "accept_major": [1],
    "min_minor": 0,
    "id_type": "string",
    "accept_features": [],
    "want_fields": ["node.p", "edge.q"],
    "client_version": "0.0.0",
}


def test_hello_welcome() -> None:
    async def inner() -> None:
        server, broadcaster = await net.start_server()
        try:
            async with websockets.connect("ws://127.0.0.1:7777/ws") as ws:
                await ws.send(json.dumps(HELLO))
                welcome = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
                assert welcome["t"] == "welcome"
                assert welcome["version"] == {"major": 1, "minor": 0}
                assert welcome["fields"] == ["node.p", "edge.q"]
        finally:
            server.close()
            await server.wait_closed()
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    asyncio.run(inner())


def test_snapshot_broadcast() -> None:
    async def inner() -> None:
        server, broadcaster = await net.start_server()
        try:
            async with websockets.connect("ws://127.0.0.1:7777/ws") as ws:
                await ws.send(json.dumps(HELLO))
                await asyncio.wait_for(ws.recv(), timeout=1)
                snapshot = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                assert snapshot["t"] == "snapshot"
                assert snapshot["nodes"] == []
                assert snapshot["pipes"] == []
                assert snapshot["meta"] == {"solve_ms": 0}
        finally:
            server.close()
            await server.wait_closed()
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    asyncio.run(inner())
