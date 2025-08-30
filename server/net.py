"""Minimal WebSocket server for the PSZCZ Flow Simulator."""

from __future__ import annotations

import asyncio
import itertools
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Set
from pathlib import Path
import contextlib

import websockets  # type: ignore[import-not-found]
from websockets.server import WebSocketServerProtocol  # type: ignore[import-not-found,attr-defined]

from .state import SimState

logger = logging.getLogger(__name__)


def _now_ms() -> int:
    """Return current time in milliseconds since Unix epoch."""
    return int(time.time() * 1000)


@dataclass
class ControlParams:
    """Runtime control parameters sent by clients."""

    pause: bool = False
    tick_hz: int = 50


@dataclass
class ServerState:
    """In-memory state shared across connections."""

    clients: Set[WebSocketServerProtocol] = field(default_factory=set)
    sent_counts: Dict[WebSocketServerProtocol, int] = field(default_factory=dict)
    recv_counts: Dict[WebSocketServerProtocol, int] = field(default_factory=dict)
    seq: itertools.count = field(default_factory=lambda: itertools.count(1))
    tick: int = 0
    control: ControlParams = field(default_factory=ControlParams)
    sim: SimState = field(default_factory=SimState)


async def _handle_client(ws: WebSocketServerProtocol, state: ServerState) -> None:
    """Handle a single client connection."""
    state.clients.add(ws)
    state.sent_counts[ws] = 0
    state.recv_counts[ws] = 0
    logger.info("client connected %s", ws.remote_address)
    try:
        raw = await ws.recv()
        state.recv_counts[ws] += 1
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await ws.close()
            return
        if msg.get("t") != "hello":
            await ws.close()
            return

        welcome = {
            "t": "welcome",
            "seq": str(next(state.seq)),
            "ts": _now_ms(),
            "version": {"major": 1, "minor": 0},
            "schema_rev": "1.0",
            "fields": ["node.p", "edge.q"],
            "use_features": [],
            "tick_hz": state.control.tick_hz,
            "server_version": "0.1.0",
        }
        await ws.send(json.dumps(welcome))
        state.sent_counts[ws] += 1

        async for raw in ws:
            state.recv_counts[ws] += 1
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:  # ignore malformed messages
                continue
            msg_type = data.get("t")
            if msg_type == "control":
                _apply_control(data, state.control)
            elif msg_type == "edit_batch":
                await _apply_edit_batch(data, ws, state)
            elif msg_type == "save":
                asyncio.create_task(_write_save(state, data.get("note", "")))
            # Unknown message types are ignored.
    except websockets.ConnectionClosed:  # pragma: no cover - connection closed
        pass
    finally:
        state.clients.discard(ws)
        sent = state.sent_counts.pop(ws, 0)
        recv = state.recv_counts.pop(ws, 0)
        logger.info("client disconnected %s sent=%d recv=%d", ws.remote_address, sent, recv)


def _apply_control(msg: Dict[str, Any], control: ControlParams) -> None:
    """Update control parameters from a control message."""
    if "pause" in msg:
        control.pause = bool(msg["pause"])
    if "tick_hz" in msg:
        try:
            control.tick_hz = int(msg["tick_hz"])
        except (TypeError, ValueError):
            pass


async def _write_save(state: ServerState, note: str) -> None:
    """Write a full snapshot to ``save-<ts>.json`` asynchronously."""
    snap = state.sim.snapshot()
    data = {
        "version": {"major": 1, "minor": 0},
        "schema_rev": "1.0",
        "tick": state.tick,
        "nodes": snap["nodes"],
        "pipes": snap["pipes"],
        "meta": {"note": note},
    }
    path = Path(f"save-{_now_ms()}.json")
    await asyncio.to_thread(path.write_text, json.dumps(data), encoding="utf-8")
    logger.info("wrote %s", path)


async def _apply_edit_batch(msg: Dict[str, Any], ws: WebSocketServerProtocol, state: ServerState) -> None:
    """Apply an edit_batch message to the simulation state."""
    edits = msg.get("edits")
    if not isinstance(edits, list):
        await _send_error(ws, state, "bad_request", "Malformed edits")
        return
    err = state.sim.apply_edits(edits)
    if err:
        await _send_error(ws, state, err["code"], "Entity id already exists" if err["code"] == "id_conflict" else "")


async def _send_error(ws: WebSocketServerProtocol, state: ServerState, code: str, message: str) -> None:
    """Send an error message to a client."""
    error = {
        "t": "error",
        "seq": str(next(state.seq)),
        "ts": _now_ms(),
        "code": code,
        "message": message,
    }
    await ws.send(json.dumps(error))
    state.sent_counts[ws] = state.sent_counts.get(ws, 0) + 1


async def _broadcast_snapshots(state: ServerState) -> None:
    """Broadcast full snapshots to all clients at the configured tick rate."""
    while True:
        start = time.perf_counter()
        if not state.control.pause:
            state.tick += 1
            snap = state.sim.snapshot()
            snapshot = {
                "t": "snapshot",
                "seq": str(next(state.seq)),
                "ts": _now_ms(),
                "tick": state.tick,
                "nodes": snap["nodes"],
                "pipes": snap["pipes"],
                "meta": {"solve_ms": 0},
            }
            message = json.dumps(snapshot)
            for ws in list(state.clients):
                try:
                    await ws.send(message)
                    state.sent_counts[ws] += 1
                except websockets.ConnectionClosed:
                    state.clients.discard(ws)
                    state.sent_counts.pop(ws, None)
                    state.recv_counts.pop(ws, None)
        elapsed = time.perf_counter() - start
        delay = max(0.0, 1.0 / max(state.control.tick_hz, 1) - elapsed)
        await asyncio.sleep(delay)


async def start_server(host: str = "127.0.0.1", port: int = 7777):
    """Start the WebSocket server and snapshot broadcaster."""
    state = ServerState()

    async def handler(ws: WebSocketServerProtocol) -> None:
        if ws.request.path != "/ws":
            await ws.close()
            return
        await _handle_client(ws, state)

    server = await websockets.serve(handler, host, port)  # type: ignore[arg-type]
    broadcaster = asyncio.create_task(_broadcast_snapshots(state))
    return server, broadcaster


async def main() -> None:
    """Run the server until interrupted."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server, broadcaster = await start_server()
    try:
        await server.wait_closed()
    finally:
        broadcaster.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await broadcaster


if __name__ == "__main__":
    asyncio.run(main())
