"""Minimal console client with text commands."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .state import ClientState

import websockets  # type: ignore[import-not-found]


logger = logging.getLogger(__name__)

# Allowed pixel materials in the simulator.
NODE_TYPES = ["stone", "space", "spring", "sink"]


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
        "accept_major": [2],
        "min_minor": 0,
        "client_version": "0.2.0",
    }


def parse_command(line: str, seq: Seq, state: ClientState) -> Optional[Dict[str, Any]]:
    """Parse a command line into a protocol message."""

    parts = line.strip().split()
    if not parts:
        return None
    cmd = parts[0]
    ts = _now_ms()
    if cmd == "set_pixel" and len(parts) in {4, 5}:
        try:
            r = int(parts[1])
            c = int(parts[2])
        except ValueError:
            return None
        material = parts[3]
        if material not in NODE_TYPES:
            return None
        op: Dict[str, Any] = {
            "op": "set_pixel",
            "r": r,
            "c": c,
            "material": material,
        }
        if len(parts) == 5:
            try:
                op["depth"] = float(parts[4])
            except ValueError:
                return None
        return {"t": "edit_grid", "seq": seq.next(), "ts": ts, "ops": [op]}
    if cmd == "set_depth" and len(parts) == 4:
        try:
            r = int(parts[1])
            c = int(parts[2])
            depth = float(parts[3])
        except ValueError:
            return None
        material = state.material_at(r, c)
        op = {"op": "set_pixel", "r": r, "c": c, "material": material, "depth": depth}
        return {"t": "edit_grid", "seq": seq.next(), "ts": ts, "ops": [op]}
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


async def _recv_loop(ws, state: ClientState) -> None:
    start = time.monotonic()
    count = 0
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:  # pragma: no cover - ignore bad messages
            continue
        t = msg.get("t")
        if t == "snapshot":
            state.update(msg)
            count += 1
            elapsed = time.monotonic() - start
            rate = count / elapsed if elapsed else 0.0
            grid = state.grid
            for row in grid:
                line = "".join(cell.get("material", "?")[0] for cell in row)
                print(line)
            print(f"rate={rate:.1f} msg/s")
        elif t == "error":
            print(json.dumps(msg))


async def _input_loop(ws, seq: Seq, state: ClientState) -> None:
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        msg = parse_command(line, seq, state)
        if msg is None:
            print("?")
            continue
        await ws.send(json.dumps(msg))


def main() -> None:
    """Connect to the server and interact via text commands."""

    parser = argparse.ArgumentParser(description="PSZCZ Flow Simulator client")
    parser.add_argument("--url", default="ws://127.0.0.1:7777/ws")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    async def runner() -> None:
        seq = Seq()
        state = ClientState()
        hello = build_hello(seq.next())
        async with websockets.connect(args.url) as ws:  # type: ignore[arg-type]
            await ws.send(json.dumps(hello))
            welcome = json.loads(await ws.recv())
            print(welcome)

            recv_task = asyncio.create_task(_recv_loop(ws, state))
            send_task = asyncio.create_task(_input_loop(ws, seq, state))
            done, pending = await asyncio.wait(
                [recv_task, send_task], return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    asyncio.run(runner())


if __name__ == "__main__":
    main()

