# PSZCZ Wire Protocol — Version 1.0

This file defines the **stable wire contract** between clients and servers. It focuses on **compatibility**, **extensibility**, and **clarity**. MVP uses **JSON over WebSocket**.

## 1) Versioning & Compatibility

- `version = { major, minor }`
- **Major**: breaking changes only (type/meaning changes).
- **Minor**: strictly **additive** (new fields/messages/enums). No removal or type change of existing fields.

### 1.1 Handshake & Feature Negotiation

Client → Server `hello` **must** include:
- `accept_major: [1]` — list of acceptable majors (MVP includes `1`).
- `min_minor: 0` — lowest minor the client supports within major 1.
- `id_type: "string"` — clients send IDs as strings.
- `accept_features: []` — e.g., later `["delta-1","ack-ids-1","zstd-1"]`.
- `want_fields: ["node.p","edge.q"]` — data fields requested in snapshots.
- `client_version: "x.y.z"` — freeform.

Server → Client `welcome` includes:
- `version: { major:1, minor:K }`
- `schema_rev: "1.K"`
- `fields: [...]` (subset the server will actually send)
- `use_features: [...]` (intersection of `accept_features` and server support)
- `tick_hz: number`
- `server_version: "x.y.z"`

If no common **major**, server sends `error { code:"incompatible_version" }` and closes.

### 1.2 Extensibility Rules (Major-1 Contract)

- **Add only**: add new fields/messages/enums; never change existing types or semantics.
- **Ignore unknowns**: both sides must ignore unknown fields and unknown message types.
- **Do not remove** fields within the same major (they may be deprecated and not sent unless requested).
- **Stable units**: Pa, m³/s, m. A unit change requires a new **major**.

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
  "accept_major": [1],
  "min_minor": 0,
  "id_type": "string",
  "accept_features": [],
  "want_fields": ["node.p", "edge.q"],
  "client_version": "0.1.0"
}
```

### 3.2 `welcome` (server → client)

```json
{
  "t": "welcome",
  "seq": "2",
  "ts": 0,
  "version": { "major": 1, "minor": 0 },
  "schema_rev": "1.0",
  "fields": ["node.p", "edge.q"],
  "use_features": [],
  "tick_hz": 50,
  "server_version": "0.1.0"
}
```

### 3.3 `edit_batch` (client → server)

Applies a set of edits atomically. In MVP the **client chooses IDs** (strings). Server rejects collisions via `error`.

Each `edit` is one of:

- `{"op":"add_node","id":"n123","type":"pump","params":{...}}`
- `{"op":"add_pipe","id":"e501","a":"n123","b":"n200","params":{...}}`
- `{"op":"set_param","id":"n123","key":"open","value":0.5}`
- `{"op":"del","id":"e501"}`

```json
{
  "t": "edit_batch",
  "seq": "10",
  "ts": 0,
  "edits": [ /* array of edits as above */ ]
}
```

> Future: feature `ack-ids-1` adds `temp_id` → `id` mapping acknowledgement.

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

**MVP uses full snapshots** only. Fields included are agreed in handshake (`fields`). Minimal payload has pressures on nodes and flows on edges. A pixel grid describing terrain and water depth may be included via the `grid` field.

```json
{
  "t": "snapshot",
  "seq": "100",
  "ts": 0,
  "tick": 12345,
  "nodes": [
    { "id":"n123", "type":"pump", "params":{ "...": "..." }, "state": { "p": 102300 } }
  ],
  "pipes": [
    { "id":"e501", "a":"n123", "b":"n200", "params":{ "...": "..." }, "state": { "q": 0.18, "dir": 1 } }
  ],
  "grid": {
    "cm_per_pixel": 1.0,
    "cells": [
      [
        {"material": "hole", "depth": 0.0},
        {"material": "brick", "depth": 0.0}
      ],
      [
        {"material": "hole", "depth": 0.5},
        {"material": "filter", "depth": 0.0}
      ]
    ]
  },
  "meta": { "solve_ms": 2.3 }
}
```

> Future: with `delta-1`, server may send only changed entities plus a periodic full.

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
  "code": "id_conflict",
  "message": "Entity id already exists"
}
```

**Stable error codes** (strings):  
`"incompatible_version"`, `"feature_not_enabled"`, `"bad_request"`, `"id_conflict"`, `"unknown_entity"`, `"unauthorized"`

## 4) Entities: Required & Optional Fields

### 4.1 Node

- **Required:** `id (string)`, `type (string)`, `params (object)`, `state (object)`
- **Node types (MVP):** `"source"`, `"sink"`, `"junction"`, `"pump"`, `"valve"`, `"accumulator"`
- **State (MVP):** `p` (pressure, Pa)
- **Params (examples, not exhaustive):**
  - `source`: `{ "target_pressure": number }`
  - `sink`: `{ "target_flow": number }`
  - `pump`: `{ "rpm": number }`
  - `valve`: `{ "open": number }` (0..1)
  - `accumulator`: `{ "capacitance": number }`
  - `junction`: `{}`

> Params/state are **maps** so new keys can be added later without breaking compatibility.

### 4.2 Pipe

- **Required:** `id (string)`, `a (string)`, `b (string)`, `params (object)`, `state (object)`
- **Params (MVP):** `{ "length": number, "diameter": number, "roughness": number, "open": number }`
- **State (MVP):** `{ "q": number, "dir": -1|0|1 }`

### 4.3 Grid Cell

- **Required:** `material (string)`, `depth (number)`
- **Materials:** `"brick"`, `"stone"`, `"hole"`, `"filter"`, `"gate"`
- **Depth:** `0.0–1.0` fraction of the cell filled with water

## 5) Units & Conventions (stable in major 1)

- Pressure `p`: **Pa**.  
- Flow `q`: **m^3/s**.  
- Length/diameter: **m**.  
- Time fields (`ts`): ms since Unix epoch.

## 6) Saves (MVP)

**File format:** one JSON object (UTF-8).  
**Required top-level fields:**

```json
{
  "version": { "major": 1, "minor": 0 },
  "schema_rev": "1.0",
  "ts": 0,
  "tick": 12345,
  "fields": ["node.p","edge.q"],
  "use_features": [],
  "nodes": [ ... ],
  "pipes": [ ... ],
  "grid": {
    "cm_per_pixel": 1.0,
    "cells": [ [ {"material": "hole", "depth": 0.0} ] ]
  },
  "meta": { "note": "optional free text" }
}
```

Clients/servers must ignore unknown fields when loading.  
Loading a different **major** is not allowed.

## 7) Control-Lock & Multi-Client

- Multiple clients may subscribe to snapshots.
- Exactly **one controlling client** is allowed to send edits/controls (MVP can hard-code this to “first client wins” or a simple toggle admin command).
- Future: authenticated roles and server-side arbitration.

## 8) Feature Flags (reserved names)

- `"delta-1"` — delta snapshots (periodic full + changes).
- `"ack-ids-1"` — server acknowledges client-proposed IDs and may remap.
- `"zstd-1"` — message compression.
