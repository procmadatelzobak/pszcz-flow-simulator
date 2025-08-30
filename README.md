# PSZCZ Flow Simulator — Seed (MVP)

Protocol-first, CPU-only **client–server** simulator for a 2D pipe-network game.  
This repository is a **seed**: minimal files, **complete specification**. All code will be generated later by Codex based solely on what’s here.

- **Server (authoritative):** headless, Linux-friendly, computes physics. For MVP: trivial placeholder physics; later: real hydraulics.
- **Client (viewer/controller):** renders the network and sends edits/controls. MVP: simplest possible Python UI; later: Godot-based client.
- **Transport:** **WebSocket** over HTTP (`ws://host:7777/ws`), **JSON** payloads in MVP. Designed to sit behind nginx for HTTPS/auth later.
- **Saves:** full-state JSON snapshot written asynchronously (no pause). Future: delta streams + replay.

> Core principle: **the wire protocol is stable and versioned**. We evolve features without breaking old clients/servers. See `PROTOCOL.md`.

## Goals (MVP)

1. Run a minimal server that:
   - Accepts WS connections.
   - Maintains in-memory graph of **nodes** and **pipes**.
   - Applies **edit batches** from a single controlling client.
   - Emits **full snapshots** at a steady tick (e.g., 20–50 Hz).
   - Writes **async full saves** on request.

2. Run a minimal client that:
   - Connects to WS, performs **hello/welcome** handshake.
   - Displays basic info from snapshots (render is intentionally simple in MVP).
   - Lets the user add nodes/pipes and change simple parameters.
   - Sends `pause/resume` and `tick rate` controls.
   - Requests a **save**.

3. Keep the protocol **forward/backward compatible** from day 0.

## Non-Goals (MVP)

- No TLS/auth (handled by reverse proxy later).
- No mixing/temperature; we reserve fields but do not compute them.
- No delta snapshots (MVP uses **full** snapshots).
- No persistence beyond on-demand saves.
- No sophisticated physics; only a placeholder step to prove the loop.

## High-Level Architecture

- **Authoritative state lives on the server.**  
  Client and server each maintain a local copy; server is the truth source.
- **Networking:** One WS endpoint `/ws`. JSON messages. Multiple clients can connect; exactly **one has control** (control-lock).
- **Ticking:** Server ticks at `tick_hz` (default 50). Snapshots broadcast at the same or a lower rate (default 20). Client interpolates if needed.
- **IDs:** On MVP, **client assigns string IDs**; server rejects collisions. Future feature `ack-ids-1` lets server reassign.

## Data Model (concept)

- **Node**: `{ id, type, params:{...}, state:{ p } }`
  - `type ∈ { "source","sink","junction","pump","valve","accumulator" }`
- **Pipe**: `{ id, a, b, params:{ length, diameter, roughness, open? }, state:{ q, dir } }`
  - `dir ∈ { -1, 0, +1 }` (flow direction sign)

**Units (stable):** pressure `Pa`, flow `m^3/s`, length `m`, diameter `m`. Changing units would require a **major** protocol bump.

## Saves (MVP)

- Asynchronously write **one full JSON snapshot** with a small header (protocol version, timestamp).
- Both client and server are allowed to write compatible saves using the same schema.

## Roadmap (post-MVP)

- Delta snapshots with feature flag `delta-1`.
- ID acknowledgements `ack-ids-1` (server authoritative ID mapping).
- Optional compression (`zstd-1`).
- Real hydraulics (sparse solvers, preconditioners), still CPU-only.
- Proper Godot client; Web export.
- Auth/TLS via nginx; server HTTP endpoints `/health`, `/save`, `/load`.

## Project layout

```
server/
    __init__.py
    net.py
    state.py
    tick.py
    io.py
client/
    __init__.py
    t0/
        __init__.py
        net.py
        ui.py
        state.py
    t1/
        __init__.py
        adapter.py
        emoji_client.py
        model.py
        serialize.py
        view.py
```

## Quick Start

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install .
python -m server.net --host 0.0.0.0 --port 7777 --health-port 7778 --tick-hz 40 &
curl http://127.0.0.1:7778/health
pszcz-client --url ws://127.0.0.1:7777/ws
# then in the client:
add_node n1 source
add_node n2 sink
add_pipe e1 n1 n2
set_param n1 target_pressure 101325
pause
resume
rate 40
save
```

The server writes `save-*.json` in its working directory.

The HTTP endpoint `GET /health` on port 7778 reports basic status information
about the running server. Example: `curl http://127.0.0.1:7778/health`.

## Clients

- **t0** – original interactive client now located under `client/t0`.
  Run with `python -m client.t0` or the `pszcz-client` wrapper.
- **t1** – read-only terminal client with emoji or ASCII output.
  Run with `python -m client.t1.emoji_client` (wrapper: `pszcz-client-start-t1`).

The previous client entry points were replaced with `python -m client.t0`.

## Automated installation

A helper script [`install_pszcz.sh`](install_pszcz.sh) bootstraps the project on
Linux systems. It clones the repository, creates isolated virtual
environments for the server and client, installs dependencies and provides
convenience wrappers for running or updating the software.

Run with defaults:

```sh
bash install_pszcz.sh
```

Override the repository URL, installation root or entry points via
environment variables:

```sh
REPO_URL="https://github.com/procmadatelzobak/pszcz-flow-simulator" \
INSTALL_ROOT="/opt/pszcz" \
SERVER_ENTRY="python -m server.net" \
CLIENT_ENTRY="python -m client.t0" \
bash install_pszcz.sh
```

The script installs helper commands:

- `pszcz-server-start` / `pszcz-server-stop`
- `pszcz-client-start` / `pszcz-client-stop`
- `pszcz-client-start-t1` – run the read-only client
- `pszcz-update` to pull the latest code and refresh dependencies

Both server and client communicate on `ws://127.0.0.1:7777/ws` by default.

### Troubleshooting

- Another application may already use port 7777.
- Ensure the virtual environment is activated.
- Firewalls may block localhost WebSocket traffic.
- Stop the server with Ctrl+C.

## Running

```sh
pszcz-server
```

The server listens on `ws://127.0.0.1:7777/ws` and broadcasts full snapshots at
the configured tick rate (default 50 Hz). On startup it auto-loads the level
`level.smoke.pump_to_drain.v1`, a simple pump-to-drain scenario used for smoke
testing.

Start the console client in another terminal:

```sh
pszcz-client
```

The client connects, prints the welcome message, then shows each snapshot tick with a running messages-per-second rate.

## Contributing

This seed repository uses a minimal continuous integration pipeline. All pull requests run:

- `pytest -q` for the test suite
- `ruff check .` for linting
- `mypy .` for static type checks

Run these commands locally before pushing changes:

```sh
pip install -r requirements.txt ruff mypy
ruff check .
mypy .
pytest -q
```

The test suite includes an integration check that starts the server on the
default port and verifies that a client can connect and receive broadcast
snapshots.

`mypy` may report that no Python files are present until code is added; this is expected in the seed.
