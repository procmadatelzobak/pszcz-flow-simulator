import asyncio
import contextlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen

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


def test_health_endpoint() -> None:
    async def inner() -> None:
        server, broadcaster = await net.start_server()
        try:
            def fetch() -> tuple[int, dict]:
                with urlopen("http://127.0.0.1:7777/health") as resp:
                    return resp.status, json.loads(resp.read().decode())

            status, data = await asyncio.to_thread(fetch)
            assert status == 200
            assert data == {"ok": True, "version": net.__version__}
        finally:
            server.close()
            await server.wait_closed()
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    asyncio.run(inner())


def test_snapshot_broadcast() -> None:
    async def inner() -> None:
        server, broadcaster = await net.start_server(snapshot_hz=5)
        try:
            async with websockets.connect("ws://127.0.0.1:7777/ws") as ws:
                await ws.send(json.dumps(HELLO))
                await asyncio.wait_for(ws.recv(), timeout=1)  # welcome
                snapshots = [
                    json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                    for _ in range(2)
                ]
                for snap in snapshots:
                    assert set(snap.keys()) == {"t", "nodes", "pipes", "version"}
                    assert snap["version"] == "mvp-0"
        finally:
            server.close()
            await server.wait_closed()
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    asyncio.run(inner())
