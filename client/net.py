"""Minimal console client with text commands."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

import websockets  # type: ignore[import-not-found]


logger = logging.getLogger(__name__)

NODE_TYPES: Set[str] = {
    "source",
    "sink",
    "junction",
    "pump",
    "valve",
    "accumulator",
}


def _now_ms() -> int:
    """Return current time in milliseconds."""
    return int(time.time() * 1000)


@dataclass
class Seq:
    """Sequence generator for `seq` fields."""

    value: int = 0

    def next(self) -> str:
        self.value += 1
        return str(self.value)


def build_hello(seq: str = "1") -> Dict[str, Any]:
    """Return a hello message following :mod:`PROTOCOL`."""

    return {
        "t": "hello",
        "seq": seq,
        "ts": _now_ms(),
        "accept_major": [1],
        "min_minor": 0,
        "id_type": "string",
        "accept_features": [],
        "want_fields": ["node.p", "edge.q"],
        "client_version": "0.1.0",
    }


def parse_command(line: str, seq: Seq) -> Optional[Dict[str, Any]]:
    """Parse a command line into a protocol message."""

    parts = line.strip().split()
    if not parts:
        return None
    cmd = parts[0]
    ts = _now_ms()
    if cmd == "add_node" and len(parts) == 3 and parts[2] in NODE_TYPES:
        edit = {
            "op": "add_node",
            "id": parts[1],
            "type": parts[2],
            "params": {},
        }
        return {"t": "edit_batch", "seq": seq.next(), "ts": ts, "edits": [edit]}
    if cmd == "add_pipe" and len(parts) == 4:
        edit = {
            "op": "add_pipe",
            "id": parts[1],
            "a": parts[2],
            "b": parts[3],
            "params": {},
        }
        return {"t": "edit_batch", "seq": seq.next(), "ts": ts, "edits": [edit]}
    if cmd == "set_param" and len(parts) >= 4:
        value_str = " ".join(parts[3:])
        try:
            value = json.loads(value_str)
        except json.JSONDecodeError:
            value = value_str
        edit = {
            "op": "set_param",
            "id": parts[1],
            "key": parts[2],
            "value": value,
        }
        return {"t": "edit_batch", "seq": seq.next(), "ts": ts, "edits": [edit]}
    if cmd == "del" and len(parts) == 2:
        edit = {"op": "del", "id": parts[1]}
        return {"t": "edit_batch", "seq": seq.next(), "ts": ts, "edits": [edit]}
    if cmd == "pause" and len(parts) == 1:
        return {"t": "control", "seq": seq.next(), "ts": ts, "pause": True}
    if cmd == "resume" and len(parts) == 1:
        return {"t": "control", "seq": seq.next(), "ts": ts, "pause": False}
    if cmd == "rate" and len(parts) == 2:
        try:
            hz = int(float(parts[1]))
        except ValueError:
            return None
        return {"t": "control", "seq": seq.next(), "ts": ts, "tick_hz": hz}
    if cmd == "save" and len(parts) == 1:
        return {"t": "save", "seq": seq.next(), "ts": ts}
    return None


async def _recv_loop(ws) -> None:
    start = time.monotonic()
    count = 0
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:  # pragma: no cover - ignore bad messages
            continue
        t = msg.get("t")
        if t == "snapshot":
            count += 1
            elapsed = time.monotonic() - start
            rate = count / elapsed if elapsed else 0.0
            tick = msg.get("tick")
            print(f"tick={tick} rate={rate:.1f} msg/s")
        elif t == "error":
            print(json.dumps(msg))


async def _input_loop(ws, seq: Seq) -> None:
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        msg = parse_command(line, seq)
        if msg is None:
            print("?")
            continue
        await ws.send(json.dumps(msg))


async def main() -> None:
    """Connect to the server and interact via text commands."""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    uri = "ws://127.0.0.1:7777/ws"
    seq = Seq()
    hello = build_hello(seq.next())
    async with websockets.connect(uri) as ws:  # type: ignore[arg-type]
        await ws.send(json.dumps(hello))
        welcome = json.loads(await ws.recv())
        print(welcome)

        recv_task = asyncio.create_task(_recv_loop(ws))
        send_task = asyncio.create_task(_input_loop(ws, seq))
        done, pending = await asyncio.wait(
            [recv_task, send_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


if __name__ == "__main__":
    asyncio.run(main())

