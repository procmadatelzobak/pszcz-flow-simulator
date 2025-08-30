from __future__ import annotations

import argparse
import time

from . import adapter, model, serialize, view


def main() -> None:
    parser = argparse.ArgumentParser(description="t1 emoji client")
    parser.add_argument("--mock", action="store_true", help="force mock adapter")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rate", type=float, default=0.5)
    parser.add_argument("--endpoint", type=str)
    parser.add_argument("--rows", type=int, default=11)
    parser.add_argument("--cols", type=int, default=36)
    parser.add_argument("--fps", type=float, default=8.0)
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--no-ansi", action="store_true")
    parser.add_argument("--map", type=str)
    parser.add_argument("--save", type=str)
    args = parser.parse_args()

    if args.map:
        state = serialize.load_map(args.map)
    else:
        state = model.default_map(args.rows, args.cols)

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
