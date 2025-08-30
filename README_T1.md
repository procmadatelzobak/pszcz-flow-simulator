# t1 Client

`t1` is a read-only terminal client that renders a simple water flow using
emoji (with an ASCII fallback). Materials and water depth are colour coded and a
legend with the current resolution is shown. It does not accept any user input
and terminates via `Ctrl+C`.

## Pixel grid

The simulation is represented as a rectangular grid of pixels. Each **pixel**
stores a `material` and the current water `depth`:

| Material | Emoji | Description |
| --- | --- | --- |
| `stone` | 🪨 | solid wall blocking the flow |
| `space` | _(empty)_ | free space where water may flow |
| `spring` | 💧 | source emitting water |
| `sink` | 🕳️ | drain removing water |

The optional `--cm-per-pixel` parameter defines the physical size represented
by one grid cell (default **1.0 cm**).

### Water depth

Water `depth` is a floating‑point value in the **0.0–1.0** range and indicates
how much of the cell is filled with water. The renderer maps the value to four
blue shades (25 % steps). Values above 1.0 are clamped to the darkest shade.

## Usage

```sh
python -m client.t1.emoji_client
```

Options:

- `--mock` / `--no-mock` – use the deterministic mock adapter (default).
- `--seed` / `--rate` – parameters for the mock adapter (defaults 123 and 0.8).
- `--endpoint ws://host:port/ws` – try to use a socket adapter; if the
  connection fails the client falls back to the mock and shows an alarm.
- `--ascii` – render using ASCII characters instead of emoji.
- `--no-ansi` – disable ANSI escape codes (useful for snapshot tests).
- `--cm-per-pixel` – physical size represented by one pixel (default 1.0 cm).
- `--map path.json` – load a map from JSON.
- `--save path.json` – export the current map to JSON.
- `--fps 5` – set refresh rate (default 8).

## Default map

Without `--map` the client loads an 8×8 demo level. The outer border uses
`stone` pixels while the centre row forms an open channel of `space`. The
second cell of the channel is a `spring` and the far end is a `sink`.

## Map format

Each map defines a 2D grid where every cell specifies the material and the
current water depth. Only `stone`, `space`, `spring` and `sink` are valid
materials. The physical resolution `cm_per_pixel` defaults to 1.0:

```json
{
  "rows": 2,
  "cols": 3,
  "cm_per_pixel": 1.0,
  "grid": [
    [
      {"material": "space", "depth": 0.0},
      {"material": "stone", "depth": 0.0},
      {"material": "spring", "depth": 1.0}
    ],
    [
      {"material": "stone", "depth": 0.0},
      {"material": "space", "depth": 0.5},
      {"material": "sink", "depth": 0.0}
    ]
  ]
}
```

### Example: mixed materials

```json
{
  "rows": 3,
  "cols": 4,
  "cm_per_pixel": 0.5,
  "grid": [
    [
      {"material": "stone", "depth": 0.0},
      {"material": "spring", "depth": 0.0},
      {"material": "space", "depth": 0.0},
      {"material": "space", "depth": 0.0}
    ],
    [
      {"material": "space", "depth": 0.0},
      {"material": "space", "depth": 0.5},
      {"material": "space", "depth": 1.0},
      {"material": "stone", "depth": 0.0}
    ],
    [
      {"material": "sink", "depth": 0.0},
      {"material": "stone", "depth": 0.0},
      {"material": "stone", "depth": 0.0},
      {"material": "stone", "depth": 0.0}
    ]
  ]
}
```

## Colour & Emoji Interface

By default the client renders the grid using coloured emoji. An ASCII
fallback can be enabled with `--ascii`.

*Screenshot omitted because binary files are not stored in this repository.*

### Limitations

- Emoji width varies between terminals; the client assumes two-column emoji
  which may not hold everywhere.
- Each frame redraws the entire screen which can impact performance on slow
  terminals.
