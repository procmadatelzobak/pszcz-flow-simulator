from __future__ import annotations

import argparse
import asyncio
import contextlib
import itertools
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Protocol, Set

import websockets  # type: ignore[import-not-found]
from aiohttp import web

from . import __version__
from .io import load_level
from .state import Pixel, SimState


class WSProtocol(Protocol):
    """Protocol representing minimal WebSocket operations used by the server."""

    remote_address: Any
    request: Any

    async def recv(self) -> str:  # pragma: no cover - interface only
        ...

    async def send(self, message: str) -> None:  # pragma: no cover - interface only
        ...

    async def close(self) -> None:  # pragma: no cover - interface only
        ...

    def __aiter__(self) -> AsyncIterator[str]:  # pragma: no cover - interface only
        ...


logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "2.0"


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

    clients: Set[WSProtocol] = field(default_factory=set)
    sent_counts: Dict[WSProtocol, int] = field(default_factory=dict)
    recv_counts: Dict[WSProtocol, int] = field(default_factory=dict)
    seq: itertools.count = field(default_factory=lambda: itertools.count(1))
    tick: int = 0
    control: ControlParams = field(default_factory=ControlParams)
    sim: SimState = field(default_factory=SimState)
    snapshot_hz: float = 20.0


async def _handle_client(ws: WSProtocol, state: ServerState) -> None:
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
            "version": {"major": 2, "minor": 0},
            "schema_rev": "2.0",
            "tick_hz": state.control.tick_hz,
            "server_version": "0.2.0",
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
            elif msg_type == "edit_grid":
                await _apply_edit_grid(data, ws, state)
            elif msg_type == "save":
                asyncio.create_task(_write_save(state, data.get("note", "")))
            # Unknown message types are ignored.
    except websockets.ConnectionClosed:  # pragma: no cover - connection closed
        pass
    finally:
        state.clients.discard(ws)
        sent = state.sent_counts.pop(ws, 0)
        recv = state.recv_counts.pop(ws, 0)
        logger.info(
            "client disconnected %s sent=%d recv=%d", ws.remote_address, sent, recv
        )


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
        "version": {"major": 2, "minor": 0},
        "schema_rev": "2.0",
        "tick": state.tick,
        "grid": {"cm_per_pixel": 1.0, "cells": snap["grid"]},
        "meta": {"note": note},
    }
    path = Path(f"save-{_now_ms()}.json")
    await asyncio.to_thread(path.write_text, json.dumps(data), encoding="utf-8")
    logger.info("wrote %s", path)


async def _apply_edit_grid(msg: Dict[str, Any], ws: WSProtocol, state: ServerState) -> None:
    edits = msg.get("ops")
    if not isinstance(edits, list):
        await _send_error(ws, state, "bad_request", "Malformed edits")
        return
    err = state.sim.apply_edits(edits)
    if err:
        await _send_error(ws, state, err["code"], "")


async def _send_error(ws: WSProtocol, state: ServerState, code: str, message: str) -> None:
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
    """Broadcast snapshots of the current simulation state."""

    while True:
        snap = state.sim.snapshot()
        payload = {
            "t": "snapshot",
            "seq": str(next(state.seq)),
            "ts": _now_ms(),
            "tick": state.tick,
            "grid": {"cm_per_pixel": 1.0, "cells": snap["grid"]},
            "version": PROTOCOL_VERSION,
        }
        message = json.dumps(payload)
        for ws in list(state.clients):
            try:
                await ws.send(message)
                state.sent_counts[ws] = state.sent_counts.get(ws, 0) + 1
            except websockets.ConnectionClosed:
                state.clients.discard(ws)
                state.sent_counts.pop(ws, None)
                state.recv_counts.pop(ws, None)
        await asyncio.sleep(1.0 / state.snapshot_hz if state.snapshot_hz > 0 else 0)


async def start_server(
    host: str = "127.0.0.1",
    port: int = 7777,
    tick_hz: float = 50.0,
    snapshot_hz: float = 20.0,
    level_path: str | Path | None = None,
    health_port: int = 7778,
):
    """Start the WebSocket and health servers plus snapshot broadcaster."""

    state = ServerState()
    state.control.tick_hz = int(tick_hz)
    state.snapshot_hz = snapshot_hz
    if level_path is not None:
        try:
            load_level(level_path, state.sim)
        except FileNotFoundError:
            logger.warning("level file %s not found; starting empty", level_path)
    if not state.sim.grid:
        state.sim.grid = [[Pixel("space", 0.0)]]

    async def handler(ws: Any) -> None:
        path = getattr(ws, "path", None)
        if path is None:
            req = getattr(ws, "request", None)
            path = getattr(req, "path", None) if req else None
        if path != "/ws":
            await ws.close()
            return
        await _handle_client(ws, state)

    app = web.Application()

    async def _health(_: web.Request) -> web.Response:
        return web.json_response(
            {
                "ok": True,
                "version": __version__,
                "tick_hz": state.control.tick_hz,
                "clients": len(state.clients),
            }
        )

    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, health_port)
    await site.start()

    server = await websockets.serve(handler, host, port)  # type: ignore[arg-type]
    broadcaster = asyncio.create_task(_broadcast_snapshots(state))
    return server, broadcaster, runner


def main() -> None:
    """Run the server until interrupted."""

    parser = argparse.ArgumentParser(description="PSZCZ Flow Simulator server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7777)
    parser.add_argument("--health-port", type=int, default=7778)
    parser.add_argument("--level", default="levels/level.smoke.pump_to_drain.v1.json")
    parser.add_argument("--tick-hz", type=int, default=50)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    async def runner() -> None:
        server, broadcaster, health = await start_server(
            host=args.host,
            port=args.port,
            tick_hz=args.tick_hz,
            level_path=args.level,
            health_port=args.health_port,
        )
        try:
            await server.wait_closed()
        finally:
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster
            await health.cleanup()

    asyncio.run(runner())


if __name__ == "__main__":
    main()

