"""Read Le Mans Ultimate / rFactor 2 telemetry from Windows named shared memory.

Requires the rF2 Shared Memory Map plugin (same as LMU). Buffer name matches the
plugin default: ``$rFactor2SMMP_Telemetry$``.

See ``docs/telemetry-format.md`` for layout and upstream references.
"""

from __future__ import annotations

import mmap
import sys

# Plugin exposes a single telemetry mapping; size is version-dependent (~115 KiB).
# Map a conservative upper bound so we do not truncate newer plugin layouts.
_TELEMETRY_BUFFER_BYTES = 200_000

# From rF2SharedMemoryMapPlugin / docs/telemetry-format.md
_RF2_TELEMETRY_MAP_NAME = "$rFactor2SMMP_Telemetry$"
_RF2_SCORING_MAP_NAME = "$rFactor2SMMP_Scoring$"


def read_rf2_telemetry_buffer() -> bytes | None:
    """Return a snapshot of the telemetry shared memory, or None if unavailable.

    Non-Windows platforms always return None (LMU is Windows-only today).
    """
    if sys.platform != "win32":
        return None

    try:
        region = mmap.mmap(-1, _TELEMETRY_BUFFER_BYTES, tagname=_RF2_TELEMETRY_MAP_NAME)
    except OSError:
        return None

    try:
        return bytes(region)
    finally:
        region.close()


def read_rf2_scoring_buffer() -> bytes | None:
    """Return a snapshot of the scoring shared memory, or None if unavailable."""
    if sys.platform != "win32":
        return None

    from src.capture.rf2_scoring_ctypes import RF2_SCORING_BUFFER_BYTES

    try:
        region = mmap.mmap(-1, RF2_SCORING_BUFFER_BYTES, tagname=_RF2_SCORING_MAP_NAME)
    except OSError:
        return None

    try:
        return bytes(region)
    finally:
        region.close()
