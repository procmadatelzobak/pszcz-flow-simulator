# Directions for Codex — Build Plan & Guardrails

This document tells Codex **exactly how to grow** the MVP from the seed specs. No source code is provided here; Codex must generate it following these rules.

## 0) Principles

- **Do not change `PROTOCOL.md` semantics** without bumping `version` per rules.
- Prefer **small, composable PRs**; keep each step shippable.
- MVP favors **simplicity over performance**; future phases will replace parts transparently.

## 1) Deliverables (MVP)

Create these runnable components **without adding new files beyond this list** unless strictly necessary:

- `server/` (Python 3.11+)
  - Headless WS server at `ws://127.0.0.1:7777/ws`.
  - In-memory state (dicts or simple classes) for a pixel grid (materials and depths).
  - Tick loop with configurable `tick_hz` (default 50).
  - Apply `edit_grid`, `control`, `save`.
  - Broadcast **full `snapshot`** to all clients at steady cadence.
  - Async save of a **full JSON** snapshot (schema as in `PROTOCOL.md`).

- `client/` (Python)
  - Connects to WS and performs `hello`/`welcome`.
  - Receives and validates `snapshot` (grid only).
  - Minimal, text-based or very simple UI to edit pixels, pause/resume, change tick rate, and request save.
  - Renders something minimal (ASCII/very basic 2D). A later PR will switch to Pygame or Godot; do not block on graphics now.

- `scripts/` (optional, later)
  - Simple launcher scripts (`run_server.sh`, `run_client.sh`) added in a later PR.

## 2) Acceptance Criteria (MVP)

1. **Connectivity**
   - Client connects to `ws://127.0.0.1:7777/ws`.
   - Handshake exchange matches `PROTOCOL.md`.
   - Unknown fields are ignored gracefully.

2. **Edits**
   - Client can send `edit_grid` with `set_pixel` operations.
   - Server validates material names and bounds; invalid requests return `error` with `code:"invalid_material"` or `"index_out_of_bounds"`.

3. **Ticking & Snapshots**
   - Server ticks at ~50 Hz with minimal jitter; broadcasts **full** grid snapshots at ≥20 Hz by default.
   - `meta.solve_ms` included (even if it’s just elapsed step time).

4. **Save (no pause)**
   - Client can send `save`.
   - Server asynchronously writes a JSON file matching `PROTOCOL.md`.
   - The sim does **not pause** during save.

5. **Multi-Client**
   - Two clients can connect; both receive snapshots.
   - Only one can control (MVP: first client gains control; second is read-only).

6. **No TLS/Auth**
   - Out of scope for MVP; keep code ready to run behind nginx later.

## 3) Guardrails & Style

- Python 3.11+, `asyncio` for WS (e.g., `websockets` or `FastAPI+uvicorn` WS route).
- Type hints, docstrings, clear module boundaries (`net`, `state`, `tick`, `io`).
- Logging with timestamps and connection IDs.
- Keep modules small and testable.
- **Do not** introduce external dependencies unrelated to WS/JSON/time unless needed.

## 4) Tests (MVP)

- Unit tests (pytest) for:
  - Handshake negotiation: `accept_major`, `min_minor`.
  - `edit_grid` validation (invalid material, out-of-range coordinates).
  - Snapshot schema sanity (required fields present; units untouched).
  - Save file round-trip (write → read basic fields).
- No integration tests with graphics yet.

## 5) Performance Targets (MVP—not strict)

- With placeholder physics, a grid of ~5k pixels should tick at 50 Hz on a mainstream desktop CPU.
- Memory use is not constrained in MVP (the future server may use far more RAM and advanced solvers).

## 6) Roadmap Tasks (post-MVP; open issues)

- Delta snapshots (`delta-1`): protocol support + implementation.
- Server-assigned IDs (`ack-ids-1`) and mapping acknowledgements.
- Optional compression (`zstd-1`).
- Simple Pygame client (zoom/pan, color overlays).
- Real hydraulics step (sparse solver), still CPU-only.
- HTTP `/health`, `/load`, and save completion callback.
- Packaging & scripts: installers, systemd unit, Dockerfile (optional).
- Godot client; later Web export.

## 7) DoD (Definition of Done)

- All AC in §2 pass locally.
- Lint/type checks pass.
- README updated with run instructions.
- Protocol examples in `PROTOCOL.md` remain valid.
- No breaking changes to existing message fields; version remains `2.0` for MVP.
