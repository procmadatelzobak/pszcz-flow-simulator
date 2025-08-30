import asyncio
import contextlib
import json
import urllib.request
from pathlib import Path
import sys
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[1]))
from server import net as server_net


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


async def test_health_endpoint() -> None:
    server, broadcaster, health = await _start()
    try:
        resp = await asyncio.to_thread(urllib.request.urlopen, "http://127.0.0.1:7778/health")
        data = json.loads(resp.read().decode())
        assert data["ok"] is True
    finally:
        await _stop(server, broadcaster, health)
