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


async def _read_until(ws, predicate):
    while True:
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
        if predicate(msg):
            return msg


def test_add_and_duplicate() -> None:
    async def inner() -> None:
        server, broadcaster = await net.start_server()
        try:
            async with websockets.connect("ws://127.0.0.1:7777/ws") as ws:
                await ws.send(json.dumps(HELLO))
                await _read_until(ws, lambda m: m["t"] == "welcome")
                await _read_until(ws, lambda m: m["t"] == "snapshot")

                edits = [
                    {"op": "add_node", "id": "n1", "type": "source", "params": {}},
                    {"op": "add_node", "id": "n2", "type": "sink", "params": {}},
                    {"op": "add_pipe", "id": "p1", "a": "n1", "b": "n2", "params": {}},
                ]
                await ws.send(json.dumps({"t": "edit_batch", "seq": "2", "ts": 0, "edits": edits}))
                snap = await _read_until(ws, lambda m: m["t"] == "snapshot" and any(n["id"] == "n1" for n in m["nodes"]))
                assert any(node["id"] == "n1" for node in snap["nodes"])
                assert any(pipe["id"] == "p1" for pipe in snap["pipes"])

                # duplicate ID
                dup = {"op": "add_node", "id": "n1", "type": "source", "params": {}}
                await ws.send(json.dumps({"t": "edit_batch", "seq": "3", "ts": 0, "edits": [dup]}))
                err = await _read_until(ws, lambda m: m.get("t") == "error")
                assert err["code"] == "id_conflict"
        finally:
            server.close()
            await server.wait_closed()
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    asyncio.run(inner())


def test_unknown_op() -> None:
    async def inner() -> None:
        server, broadcaster = await net.start_server()
        try:
            async with websockets.connect("ws://127.0.0.1:7777/ws") as ws:
                await ws.send(json.dumps(HELLO))
                await _read_until(ws, lambda m: m["t"] == "welcome")
                await _read_until(ws, lambda m: m["t"] == "snapshot")

                bad = {"op": "bogus"}
                await ws.send(json.dumps({"t": "edit_batch", "seq": "2", "ts": 0, "edits": [bad]}))
                err = await _read_until(ws, lambda m: m.get("t") == "error")
                assert err["code"] == "bad_request"
        finally:
            server.close()
            await server.wait_closed()
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    asyncio.run(inner())
