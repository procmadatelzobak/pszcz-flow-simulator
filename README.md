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
