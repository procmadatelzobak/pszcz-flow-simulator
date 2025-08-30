import asyncio
import contextlib
import json
from pathlib import Path
import sys
from typing import Any

import websockets

sys.path.append(str(Path(__file__).resolve().parents[1]))
from server import net as server_net
from client.net import build_hello


async def _start() -> tuple[asyncio.AbstractServer, asyncio.Task, Any]:
    server, broadcaster, health = await server_net.start_server()
    return server, broadcaster, health


async def _stop(server: asyncio.AbstractServer, broadcaster: asyncio.Task, health: Any) -> None:
    server.close()
    await server.wait_closed()
    broadcaster.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await broadcaster
    await health.cleanup()


async def test_ws_roundtrip() -> None:
    server, broadcaster, health = await _start()
    try:
        async with websockets.connect("ws://127.0.0.1:7777/ws") as ws:
            await ws.send(json.dumps(build_hello()))
            welcome = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
            assert welcome["t"] == "welcome"
            snapshot = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
            assert "grid" in snapshot and "cells" in snapshot["grid"]
            ops = [{"op": "set_pixel", "r": 0, "c": 0, "material": "spring"}]
            await ws.send(json.dumps({"t": "edit_grid", "seq": "2", "ts": 0, "ops": ops}))
            errors = []
            end = asyncio.get_running_loop().time() + 0.5
            while asyncio.get_running_loop().time() < end:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=end - asyncio.get_running_loop().time())
                    data = json.loads(msg)
                    if data.get("t") == "error":
                        errors.append(data)
                except asyncio.TimeoutError:
                    break
            assert not errors
    finally:
        await _stop(server, broadcaster, health)

