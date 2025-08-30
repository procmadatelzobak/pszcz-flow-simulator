"""t0 client for PSZCZ Flow Simulator (deprecated).

This legacy client is kept for reference only and is no longer maintained.
Use :mod:`client.t1` instead.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "client.t0 is deprecated and will be removed; use client.t1 instead",
    DeprecationWarning,
    stacklevel=2,
)
