import asyncio
import contextlib
import json
from pathlib import Path
import sys

import websockets  # type: ignore[import-not-found]

sys.path.append(str(Path(__file__).resolve().parents[1]))
from server import net as server_net
from client.t0 import net as client_net


def test_server_client_handshake() -> None:
    async def inner() -> None:
        server, broadcaster = await server_net.start_server()
        try:
            async with websockets.connect("ws://127.0.0.1:7777/ws") as ws:
                await ws.send(json.dumps(client_net.build_hello()))
                welcome = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
                assert welcome["t"] == "welcome"
                snapshot = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                assert snapshot["t"] == "snapshot"
        finally:
            server.close()
            await server.wait_closed()
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    asyncio.run(inner())
