"""Command-line client rendering the pixel grid using emoji or ASCII.

Supports optional WebSocket connection, map import/export and configurable
physical resolution via ``--cm-per-pixel``.
"""

from __future__ import annotations

import argparse
import time

from . import adapter, model, serialize, view


def main() -> None:
    parser = argparse.ArgumentParser(description="t1 emoji client")
    parser.add_argument(
        "--mock",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="use mock adapter (default)",
    )
    parser.add_argument("--seed", type=int, default=123, help="PRNG seed")
    parser.add_argument("--rate", type=float, default=0.8, help="mock event rate")
    parser.add_argument("--endpoint", type=str)
    parser.add_argument("--rows", type=int, default=11)
    parser.add_argument("--cols", type=int, default=36)
    parser.add_argument("--fps", type=float, default=8.0)
    parser.add_argument("--cm-per-pixel", type=float, default=1.0, help="resolution in cm per pixel")
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--no-ansi", action="store_true")
    parser.add_argument("--map", type=str)
    parser.add_argument("--save", type=str)
    args = parser.parse_args()

    if args.map:
        state = serialize.load_map(args.map)
        state.cm_per_pixel = args.cm_per_pixel
    else:
        state = model.default_map(args.rows, args.cols, cm_per_pixel=args.cm_per_pixel)

    if args.save:
        serialize.save_map(state, args.save)

    mock = adapter.MockAdapter(seed=args.seed, rate=args.rate)
    source: adapter.MockAdapter | adapter.SocketAdapter = mock
    if args.endpoint and not args.mock:
        source = adapter.SocketAdapter(args.endpoint, mock)

    try:
        while True:
            snap = source.snapshot()
            frame = view.render(state, snap, ascii=args.ascii, no_ansi=args.no_ansi)
            print(frame, end="", flush=True)
            time.sleep(1.0 / max(args.fps, 1.0))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":  # pragma: no cover
    main()
