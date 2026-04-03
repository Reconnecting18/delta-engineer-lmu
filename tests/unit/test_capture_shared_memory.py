"""Tests for LMU shared-memory reader."""

import sys

from src.capture.lmu_shared_memory import read_rf2_telemetry_buffer


def test_read_rf2_telemetry_buffer_smoke() -> None:
    if sys.platform == "win32":
        # Windows CI / dev: mapping may or may not exist; just ensure no crash.
        read_rf2_telemetry_buffer()
    else:
        assert read_rf2_telemetry_buffer() is None
