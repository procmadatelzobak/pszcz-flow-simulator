import asyncio
import contextlib
import json
import sys
from pathlib import Path

import websockets  # type: ignore[import-not-found]

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


def test_save(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(net, "_now_ms", lambda: 0)

    async def inner() -> None:
        server, broadcaster = await net.start_server()
        try:
            async with websockets.connect("ws://127.0.0.1:7777/ws") as ws:
                await ws.send(json.dumps(HELLO))
                await ws.recv()  # welcome
                await ws.recv()  # first snapshot
                await ws.send(json.dumps({"t": "save", "seq": "2", "ts": 0}))
                await asyncio.sleep(0.1)
                path = tmp_path / "save-0.json"
                assert path.exists()
                data = json.loads(path.read_text())
                assert "nodes" in data and "pipes" in data and "meta" in data
        finally:
            server.close()
            await server.wait_closed()
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    asyncio.run(inner())

