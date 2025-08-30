# PSZCZ Wire Protocol — Version 2.0

This file defines the **stable wire contract** between clients and servers. It focuses on **compatibility**, **extensibility**,
and **clarity**. Communication uses **JSON over WebSocket**.

## 1) Versioning & Compatibility

- `version = { major, minor }`
- **Major**: breaking changes only.
- **Minor**: strictly **additive**.

### 1.1 Handshake

Client → Server `hello` **must** include:
- `accept_major: [2]` — list of acceptable majors (MVP includes `2`).
- `min_minor: 0` — lowest minor the client supports within major 2.
- `client_version: "x.y.z"` — freeform.

Server → Client `welcome` includes:
- `version: { major:2, minor:K }`
- `schema_rev: "2.K"`
- `tick_hz: number`
- `server_version: "x.y.z"`

If no common **major**, server sends `error { code:"incompatible_version" }` and closes.

### 1.2 Extensibility Rules (Major-2 Contract)

- **Add only**: add new fields/messages/enums; never change existing types or semantics.
- **Ignore unknowns**: both sides must ignore unknown fields and unknown message types.
- **Do not remove** fields within the same major (they may be deprecated and not sent unless requested).
- **Stable units**: depth is measured in metres. A unit change requires a new **major**.

## 2) Envelope & Common Fields

Every message is a JSON object with at least:

- `t` — message type (string), e.g., `"hello"`, `"welcome"`, `"snapshot"`.
- `seq` — monotonically increasing sequence number (int or string).
- `ts` — server timestamp in milliseconds since Unix epoch (number).

Unknown `t` values must be ignored safely.

## 3) Message Types (MVP)

### 3.1 `hello` (client → server)

```json
{
  "t": "hello",
  "seq": "1",
  "ts": 0,
  "accept_major": [2],
  "min_minor": 0,
  "client_version": "0.2.0"
}
```

### 3.2 `welcome` (server → client)

```json
{
  "t": "welcome",
  "seq": "2",
  "ts": 0,
  "version": { "major": 2, "minor": 0 },
  "schema_rev": "2.0",
  "tick_hz": 50,
  "server_version": "0.2.0"
}
```

### 3.3 `edit_grid` (client → server)

Applies pixel edits atomically. Each operation is:

- `{ "op": "set_pixel", "r": 0, "c": 1, "material": "stone", "depth": 0.0 }`

`depth` is optional and defaults to `0.0`.

```json
{
  "t": "edit_grid",
  "seq": "10",
  "ts": 0,
  "ops": [
    { "op": "set_pixel", "r": 0, "c": 1, "material": "spring", "depth": 0.0 }
  ]
}
```

### 3.4 `control` (client → server)

```json
{
  "t": "control",
  "seq": "11",
  "ts": 0,
  "pause": false,
  "tick_hz": 50
}
```

Both fields are optional; server applies only provided keys.

### 3.5 `snapshot` (server → clients)

**MVP uses full snapshots** only, containing just the pixel grid.

```json
{
  "t": "snapshot",
  "seq": "100",
  "ts": 0,
  "tick": 12345,
  "grid": {
    "cm_per_pixel": 1.0,
    "cells": [
      [ { "material": "space", "depth": 0.0 }, { "material": "stone", "depth": 0.0 } ],
      [ { "material": "spring", "depth": 0.5 }, { "material": "sink", "depth": 0.0 } ]
    ]
  },
  "meta": { "solve_ms": 2.3 }
}
```

> Future: with `delta-1`, server may send only changed cells plus a periodic full.

### 3.6 `save` (client → server)

```json
{
  "t": "save",
  "seq": "50",
  "ts": 0,
  "note": "optional description"
}
```

Server performs an **async** save and may log the file path (MVP: no reply is required, but a future `save_done` may be added).

### 3.7 `error` (server → client)

```json
{
  "t": "error",
  "seq": "x",
  "ts": 0,
  "code": "invalid_material",
  "message": "Material not recognised"
}
```

**Stable error codes** (strings): `"incompatible_version"`, `"feature_not_enabled"`, `"bad_request"`, `"invalid_material"`, `"index_out_of_bounds"`, `"unauthorized"`

## 4) Grid Cells

- **Required:** `material (string)`, `depth (number)`
- **Materials:**
  - `stone` — impenetrable.
  - `space` — empty traversable cell.
  - `spring` — source of water.
  - `sink` — drains water.
- **Depth:** `0.0–1.0` fraction of the cell filled with water

## 5) Units & Conventions (stable in major 2)

- Water depth: **m**.
- Time fields (`ts`): ms since Unix epoch.

## 6) Saves (MVP)

**File format:** one JSON object (UTF-8).
**Required top-level fields:**

```json
{
  "version": { "major": 2, "minor": 0 },
  "schema_rev": "2.0",
  "ts": 0,
  "tick": 12345,
  "grid": {
    "cm_per_pixel": 1.0,
    "cells": [ [ {"material": "space", "depth": 0.0} ] ]
  },
  "meta": { "note": "optional free text" }
}
```

Clients/servers must ignore unknown fields when loading.
Loading a different **major** is not allowed.

## 7) Control-Lock & Multi-Client

- Multiple clients may subscribe to snapshots.
- Exactly **one controlling client** is allowed to send edits/controls (MVP can hard-code this to "first client wins" or a simple toggle admin command).
- Future: authenticated roles and server-side arbitration.

## 8) Feature Flags (reserved names)

- `"delta-1"` — delta snapshots (periodic full + changes).
- `"zstd-1"` — message compression.
