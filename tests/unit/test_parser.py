"""Unit tests for the telemetry parser module."""

from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from src.core.parser import (
    HEADER_FORMAT,
    HEADER_SIZE,
    KELVIN_OFFSET,
    MS_TO_KMH,
    NUM_VEHICLES_FORMAT,
    NUM_VEHICLES_SIZE,
    VEHICLE_TELEM_SIZE,
    TelemetryParseError,
    map_rf2_to_frame,
    map_session_type,
    parse_telemetry_batch,
    parse_telemetry_frame,
    parse_telemetry_header,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def sample_rf2_data() -> dict:
    """Load sample rF2 telemetry data from fixture file."""
    with open(FIXTURES_DIR / "sample_telemetry_frame.json") as f:
        return json.load(f)


@pytest.fixture
def minimal_rf2_data() -> dict:
    """Minimal rF2 data with required fields."""
    return {
        "mUnfilteredThrottle": 0.5,
        "mUnfilteredBrake": 0.3,
        "mUnfilteredSteering": 0.0,
        "mGear": 3,
        "mSpeed": 50.0,
        "mEngineRPM": 6000.0,
        "mPos": {"x": 0.0, "y": 0.0, "z": 0.0},
        "mLapNumber": 1,
        "mSector": 0,
        "mFuel": 60.0,
        "timestamp": "2026-03-24T12:00:00Z",
    }


def _build_binary_buffer(num_vehicles: int = 1, version: int = 1) -> bytes:
    """Build a minimal binary telemetry buffer for testing."""
    header = struct.pack(HEADER_FORMAT, version, version, 0)
    num_v = struct.pack(NUM_VEHICLES_FORMAT, num_vehicles)
    # Create vehicle blocks filled with zeros (default field values)
    vehicles = b"\x00" * (VEHICLE_TELEM_SIZE * num_vehicles)
    return header + num_v + vehicles


# --- map_rf2_to_frame tests ---


class TestMapRf2ToFrame:
    def test_basic_mapping(self, sample_rf2_data: dict):
        frame = map_rf2_to_frame(sample_rf2_data)
        assert frame.throttle == 0.85
        assert frame.brake == 0.0
        assert frame.steering == pytest.approx(-0.12)
        assert frame.gear == 4
        assert frame.lap_number == 3
        assert frame.sector == 2
        assert frame.fuel_level == 42.5

    def test_speed_conversion(self, sample_rf2_data: dict):
        """Speed should be converted from m/s to km/h."""
        frame = map_rf2_to_frame(sample_rf2_data)
        expected_kmh = 68.22 * MS_TO_KMH
        assert frame.speed == pytest.approx(expected_kmh)

    def test_tire_temp_conversion(self, sample_rf2_data: dict):
        """Tire temps should be converted from Kelvin to Celsius."""
        frame = map_rf2_to_frame(sample_rf2_data)
        assert frame.tire_temps is not None
        assert frame.tire_temps.front_left == pytest.approx(
            368.35 - KELVIN_OFFSET
        )
        assert frame.tire_temps.front_right == pytest.approx(
            369.25 - KELVIN_OFFSET
        )
        assert frame.tire_temps.rear_left == pytest.approx(
            371.15 - KELVIN_OFFSET
        )
        assert frame.tire_temps.rear_right == pytest.approx(
            370.65 - KELVIN_OFFSET
        )

    def test_tire_pressures_direct(self, sample_rf2_data: dict):
        """Tire pressures should pass through directly (kPa)."""
        frame = map_rf2_to_frame(sample_rf2_data)
        assert frame.tire_pressures is not None
        assert frame.tire_pressures.front_left == 172.0
        assert frame.tire_pressures.front_right == 173.0
        assert frame.tire_pressures.rear_left == 165.0
        assert frame.tire_pressures.rear_right == 166.0

    def test_position_mapping(self, sample_rf2_data: dict):
        frame = map_rf2_to_frame(sample_rf2_data)
        assert frame.position_x == 1234.56
        assert frame.position_y == 12.34
        assert frame.position_z == -567.89

    def test_weather_dry(self, sample_rf2_data: dict):
        frame = map_rf2_to_frame(sample_rf2_data)
        assert frame.weather_conditions == "dry"

    def test_weather_wet(self, minimal_rf2_data: dict):
        minimal_rf2_data["mRaining"] = 0.8
        frame = map_rf2_to_frame(minimal_rf2_data)
        assert frame.weather_conditions == "wet"

    def test_weather_mixed(self, minimal_rf2_data: dict):
        minimal_rf2_data["mRaining"] = 0.3
        frame = map_rf2_to_frame(minimal_rf2_data)
        assert frame.weather_conditions == "mixed"

    def test_weather_none_when_missing(self, minimal_rf2_data: dict):
        frame = map_rf2_to_frame(minimal_rf2_data)
        assert frame.weather_conditions is None

    def test_no_tire_data_when_missing(self, minimal_rf2_data: dict):
        frame = map_rf2_to_frame(minimal_rf2_data)
        assert frame.tire_temps is None
        assert frame.tire_pressures is None

    def test_clamps_out_of_range_throttle(self, minimal_rf2_data: dict):
        minimal_rf2_data["mUnfilteredThrottle"] = 1.5
        frame = map_rf2_to_frame(minimal_rf2_data)
        assert frame.throttle == 1.0

    def test_clamps_out_of_range_brake(self, minimal_rf2_data: dict):
        minimal_rf2_data["mUnfilteredBrake"] = -0.1
        frame = map_rf2_to_frame(minimal_rf2_data)
        assert frame.brake == 0.0

    def test_clamps_out_of_range_steering(self, minimal_rf2_data: dict):
        minimal_rf2_data["mUnfilteredSteering"] = -1.5
        frame = map_rf2_to_frame(minimal_rf2_data)
        assert frame.steering == -1.0

    def test_session_id_is_none_by_default(self, minimal_rf2_data: dict):
        frame = map_rf2_to_frame(minimal_rf2_data)
        assert frame.session_id is None


# --- parse_telemetry_header tests ---


class TestParseHeader:
    def test_valid_header(self):
        raw = struct.pack(HEADER_FORMAT, 5, 5, 1024)
        header = parse_telemetry_header(raw)
        assert header.version_update_begin == 5
        assert header.version_update_end == 5
        assert header.bytes_updated_hint == 1024

    def test_buffer_too_small(self):
        with pytest.raises(TelemetryParseError, match="Buffer too small"):
            parse_telemetry_header(b"\x00\x00")


# --- parse_telemetry_frame tests ---


class TestParseTelemetryFrame:
    def test_parse_single_vehicle(self):
        raw = _build_binary_buffer(num_vehicles=1)
        frame = parse_telemetry_frame(raw, vehicle_index=0)
        assert frame.throttle == 0.0
        assert frame.speed == 0.0

    def test_vehicle_index_out_of_range(self):
        raw = _build_binary_buffer(num_vehicles=1)
        with pytest.raises(TelemetryParseError, match="out of range"):
            parse_telemetry_frame(raw, vehicle_index=5)

    def test_mid_update_raises(self):
        """If version begin != end, buffer is mid-update."""
        header = struct.pack(HEADER_FORMAT, 5, 6, 0)
        num_v = struct.pack(NUM_VEHICLES_FORMAT, 1)
        vehicles = b"\x00" * VEHICLE_TELEM_SIZE
        raw = header + num_v + vehicles
        with pytest.raises(TelemetryParseError, match="mid-update"):
            parse_telemetry_frame(raw)

    def test_truncated_buffer(self):
        raw = struct.pack(HEADER_FORMAT, 1, 1, 0) + struct.pack(
            NUM_VEHICLES_FORMAT, 1
        )
        # No vehicle data follows
        with pytest.raises(TelemetryParseError, match="too small"):
            parse_telemetry_frame(raw)


# --- parse_telemetry_batch tests ---


class TestParseTelemetryBatch:
    def test_parse_multiple_vehicles(self):
        raw = _build_binary_buffer(num_vehicles=3)
        frames = parse_telemetry_batch(raw)
        assert len(frames) == 3

    def test_empty_buffer_zero_vehicles(self):
        raw = _build_binary_buffer(num_vehicles=0)
        frames = parse_telemetry_batch(raw)
        assert len(frames) == 0


# --- map_session_type tests ---


class TestMapSessionType:
    def test_practice_sessions(self):
        for i in [0, 1, 2, 3, 4, 9]:
            assert map_session_type(i) == "practice"

    def test_qualifying_sessions(self):
        for i in [5, 6, 7, 8]:
            assert map_session_type(i) == "qualifying"

    def test_race_sessions(self):
        for i in [10, 11, 12, 13]:
            assert map_session_type(i) == "race"

    def test_unknown_session(self):
        assert map_session_type(99) == "unknown"
