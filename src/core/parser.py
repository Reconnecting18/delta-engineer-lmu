"""Raw telemetry parser for rF2/LMU shared memory data.

Converts rF2 native field names and units into our TelemetryFrameCreate schema.
Supports both pre-parsed JSON (with rF2 field names) and raw binary dumps.

References:
- https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin
- https://github.com/TonyWhitley/pyRfactor2SharedMemory
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import UTC, datetime

from src.models.schemas import TelemetryFrameCreate, TireData

# --- Constants ---

# Wheel indices: FL=0, FR=1, RL=2, RR=3
WHEEL_FL, WHEEL_FR, WHEEL_RL, WHEEL_RR = 0, 1, 2, 3

KELVIN_OFFSET = 273.15
MS_TO_KMH = 3.6

# rF2 session type mapping
RF2_SESSION_TYPE_MAP: dict[int, str] = {
    0: "practice",   # Test day
    1: "practice",   # Practice 1
    2: "practice",   # Practice 2
    3: "practice",   # Practice 3
    4: "practice",   # Practice 4
    5: "qualifying",  # Qualifying 1
    6: "qualifying",  # Qualifying 2
    7: "qualifying",  # Qualifying 3
    8: "qualifying",  # Qualifying 4
    9: "practice",   # Warmup
    10: "race",      # Race 1
    11: "race",      # Race 2
    12: "race",      # Race 3
    13: "race",      # Race 4
}

# Binary struct layout for the telemetry buffer header
# Version info: mVersionUpdateBegin(i), mVersionUpdateEnd(i), mBytesUpdatedHint(i)
HEADER_FORMAT = "<iii"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# After header: mNumVehicles (int)
NUM_VEHICLES_FORMAT = "<i"
NUM_VEHICLES_SIZE = struct.calcsize(NUM_VEHICLES_FORMAT)

# Simplified vehicle telemetry struct layout (key fields only).
# Full rF2VehicleTelemetry is ~1800 bytes; we extract what our schema needs.
# Offsets are relative to the start of each vehicle's data block.
#
# This is a simplified extraction — the exact offsets come from the rF2 header:
# https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin/blob/master/Include/rFactor2SharedMemoryMap.hpp
VEHICLE_TELEM_SIZE = 1800  # Approximate size per vehicle

# Offsets within rF2VehicleTelemetry for key fields (double = 8 bytes, int = 4 bytes)
# These are approximate and may vary by plugin version
FIELD_OFFSETS = {
    "mElapsedTime": (0, "d"),        # c_double
    "mLapNumber": (8, "i"),          # c_int
    "mLapStartET": (12, "d"),        # c_double
    "mGear": (44, "i"),              # c_int
    "mEngineRPM": (48, "d"),         # c_double
    "mSpeed": (280, "d"),            # c_double
    "mUnfilteredThrottle": (288, "d"),
    "mUnfilteredBrake": (296, "d"),
    "mUnfilteredSteering": (304, "d"),
    "mPos_x": (312, "d"),
    "mPos_y": (320, "d"),
    "mPos_z": (328, "d"),
    "mFuel": (480, "d"),
    # Wheel data starts at offset ~500, each wheel block is ~200 bytes
    # We extract tire temp (middle) and pressure for each wheel
}

# Wheel block offsets (relative to wheel array start at ~500)
WHEEL_ARRAY_OFFSET = 500
WHEEL_BLOCK_SIZE = 200
WHEEL_PRESSURE_OFFSET = 0     # mPressure within wheel block
WHEEL_TEMP_OFFSET = 8         # mTemperature[0] (inner), +8 = middle, +16 = outer


# --- Exceptions ---


class TelemetryParseError(Exception):
    """Raised when telemetry data cannot be parsed."""

    def __init__(self, message: str, partial_results: list | None = None):
        super().__init__(message)
        self.message = message
        self.partial_results = partial_results or []


# --- Data classes ---


@dataclass
class RawTelemetryHeader:
    version_update_begin: int
    version_update_end: int
    bytes_updated_hint: int


# --- Public API ---


def map_rf2_to_frame(rf2_data: dict) -> TelemetryFrameCreate:
    """Map rF2 native field names and units to our TelemetryFrameCreate schema.

    Accepts a dict with rF2-style field names (e.g. mUnfilteredThrottle)
    and converts to our schema field names and units.

    Args:
        rf2_data: Dict with rF2 native field names.

    Returns:
        TelemetryFrameCreate with converted values.

    Raises:
        TelemetryParseError: If required fields are missing or invalid.
    """
    try:
        # Convert speed: m/s → km/h
        speed_ms = rf2_data.get("mSpeed", 0.0)
        speed_kmh = speed_ms * MS_TO_KMH

        # Convert tire temperatures: Kelvin → Celsius (use middle temp index [1])
        tire_temps = _extract_tire_temps(rf2_data)
        tire_pressures = _extract_tire_pressures(rf2_data)

        # Convert elapsed time to datetime
        elapsed_time = rf2_data.get("mElapsedTime", 0.0)
        timestamp = rf2_data.get("timestamp")
        if timestamp is None:
            timestamp = datetime.now(UTC)

        # Weather mapping
        weather = _map_weather(rf2_data)

        return TelemetryFrameCreate(
            timestamp=timestamp,
            lap_number=rf2_data.get("mLapNumber", 0),
            sector=rf2_data.get("mSector", 0),
            throttle=_clamp(rf2_data.get("mUnfilteredThrottle", 0.0), 0.0, 1.0),
            brake=_clamp(rf2_data.get("mUnfilteredBrake", 0.0), 0.0, 1.0),
            steering=_clamp(rf2_data.get("mUnfilteredSteering", 0.0), -1.0, 1.0),
            gear=rf2_data.get("mGear", 0),
            speed=speed_kmh,
            rpm=rf2_data.get("mEngineRPM", 0.0),
            position_x=rf2_data.get("mPos", {}).get("x", 0.0),
            position_y=rf2_data.get("mPos", {}).get("y", 0.0),
            position_z=rf2_data.get("mPos", {}).get("z", 0.0),
            tire_temps=tire_temps,
            tire_pressures=tire_pressures,
            fuel_level=rf2_data.get("mFuel", 0.0),
            weather_conditions=weather,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise TelemetryParseError(f"Failed to map rF2 data: {e}") from e


def parse_telemetry_header(raw: bytes) -> RawTelemetryHeader:
    """Parse the shared memory buffer header.

    Args:
        raw: Raw bytes from the start of the telemetry buffer.

    Returns:
        RawTelemetryHeader with version and update info.

    Raises:
        TelemetryParseError: If buffer is too small.
    """
    if len(raw) < HEADER_SIZE:
        raise TelemetryParseError(
            f"Buffer too small for header: {len(raw)} < {HEADER_SIZE}"
        )

    begin, end, hint = struct.unpack_from(HEADER_FORMAT, raw, 0)
    return RawTelemetryHeader(
        version_update_begin=begin,
        version_update_end=end,
        bytes_updated_hint=hint,
    )


def parse_telemetry_frame(
    raw: bytes, vehicle_index: int = 0
) -> TelemetryFrameCreate:
    """Parse a single vehicle's telemetry from a raw shared memory dump.

    Args:
        raw: Full telemetry buffer bytes.
        vehicle_index: Which vehicle to extract (0 = player).

    Returns:
        TelemetryFrameCreate for the specified vehicle.

    Raises:
        TelemetryParseError: If data is malformed or too small.
    """
    header = parse_telemetry_header(raw)
    if header.version_update_begin != header.version_update_end:
        raise TelemetryParseError(
            "Buffer is mid-update (version mismatch), retry on next tick"
        )

    offset_after_header = HEADER_SIZE + NUM_VEHICLES_SIZE
    if len(raw) < offset_after_header:
        raise TelemetryParseError("Buffer too small to read vehicle count")

    (num_vehicles,) = struct.unpack_from(NUM_VEHICLES_FORMAT, raw, HEADER_SIZE)

    if vehicle_index >= num_vehicles:
        raise TelemetryParseError(
            f"Vehicle index {vehicle_index} out of range (0-{num_vehicles - 1})"
        )

    vehicle_offset = offset_after_header + (vehicle_index * VEHICLE_TELEM_SIZE)
    if len(raw) < vehicle_offset + VEHICLE_TELEM_SIZE:
        raise TelemetryParseError(
            f"Buffer too small for vehicle {vehicle_index}"
        )

    return _parse_vehicle_block(raw, vehicle_offset)


def parse_telemetry_batch(raw: bytes) -> list[TelemetryFrameCreate]:
    """Parse all vehicles from a full telemetry buffer.

    Args:
        raw: Full telemetry buffer bytes.

    Returns:
        List of TelemetryFrameCreate, one per vehicle.

    Raises:
        TelemetryParseError: If buffer is malformed. May include partial_results.
    """
    header = parse_telemetry_header(raw)
    if header.version_update_begin != header.version_update_end:
        raise TelemetryParseError("Buffer is mid-update (version mismatch)")

    offset_after_header = HEADER_SIZE + NUM_VEHICLES_SIZE
    if len(raw) < offset_after_header:
        raise TelemetryParseError("Buffer too small to read vehicle count")

    (num_vehicles,) = struct.unpack_from(NUM_VEHICLES_FORMAT, raw, HEADER_SIZE)

    results: list[TelemetryFrameCreate] = []
    errors: list[str] = []

    for i in range(num_vehicles):
        vehicle_offset = offset_after_header + (i * VEHICLE_TELEM_SIZE)
        try:
            frame = _parse_vehicle_block(raw, vehicle_offset)
            results.append(frame)
        except (struct.error, TelemetryParseError) as e:
            errors.append(f"Vehicle {i}: {e}")

    if errors and not results:
        raise TelemetryParseError(
            f"All vehicles failed to parse: {'; '.join(errors)}"
        )

    if errors:
        raise TelemetryParseError(
            f"Some vehicles failed to parse: {'; '.join(errors)}",
            partial_results=results,
        )

    return results


def map_session_type(rf2_session: int) -> str:
    """Map rF2 session integer to our SessionType string."""
    return RF2_SESSION_TYPE_MAP.get(rf2_session, "unknown")


# --- Private helpers ---


def _parse_vehicle_block(
    raw: bytes, offset: int
) -> TelemetryFrameCreate:
    """Extract a TelemetryFrameCreate from a vehicle data block."""
    rf2_data: dict = {}

    for field_name, (field_offset, fmt) in FIELD_OFFSETS.items():
        abs_offset = offset + field_offset
        size = struct.calcsize(fmt)
        if abs_offset + size > len(raw):
            continue
        (value,) = struct.unpack_from(f"<{fmt}", raw, abs_offset)
        rf2_data[field_name] = value

    # Handle position as nested dict for map_rf2_to_frame
    rf2_data["mPos"] = {
        "x": rf2_data.pop("mPos_x", 0.0),
        "y": rf2_data.pop("mPos_y", 0.0),
        "z": rf2_data.pop("mPos_z", 0.0),
    }

    # Extract wheel data
    _extract_wheel_data_binary(raw, offset, rf2_data)

    return map_rf2_to_frame(rf2_data)


def _extract_wheel_data_binary(
    raw: bytes, vehicle_offset: int, rf2_data: dict
) -> None:
    """Extract tire temps and pressures from binary wheel data."""
    wheel_base = vehicle_offset + WHEEL_ARRAY_OFFSET
    temps_k: list[float] = []
    pressures: list[float] = []

    for i in range(4):
        wheel_offset = wheel_base + (i * WHEEL_BLOCK_SIZE)

        # Pressure
        p_offset = wheel_offset + WHEEL_PRESSURE_OFFSET
        if p_offset + 8 <= len(raw):
            (pressure,) = struct.unpack_from("<d", raw, p_offset)
            pressures.append(pressure)
        else:
            pressures.append(0.0)

        # Temperature (middle = index 1, offset +8 from temp array start)
        t_offset = wheel_offset + WHEEL_TEMP_OFFSET + 8  # middle temp
        if t_offset + 8 <= len(raw):
            (temp,) = struct.unpack_from("<d", raw, t_offset)
            temps_k.append(temp)
        else:
            temps_k.append(0.0)

    rf2_data["mWheels"] = {
        "temps_k": temps_k,
        "pressures": pressures,
    }


def _extract_tire_temps(rf2_data: dict) -> TireData | None:
    """Extract tire temperatures from rF2 data, converting K → C."""
    wheels = rf2_data.get("mWheels")
    if not wheels:
        return None

    temps_k = wheels.get("temps_k")
    if not temps_k or len(temps_k) < 4:
        return None

    return TireData(
        front_left=temps_k[WHEEL_FL] - KELVIN_OFFSET,
        front_right=temps_k[WHEEL_FR] - KELVIN_OFFSET,
        rear_left=temps_k[WHEEL_RL] - KELVIN_OFFSET,
        rear_right=temps_k[WHEEL_RR] - KELVIN_OFFSET,
    )


def _extract_tire_pressures(rf2_data: dict) -> TireData | None:
    """Extract tire pressures from rF2 data (already in kPa)."""
    wheels = rf2_data.get("mWheels")
    if not wheels:
        return None

    pressures = wheels.get("pressures")
    if not pressures or len(pressures) < 4:
        return None

    return TireData(
        front_left=pressures[WHEEL_FL],
        front_right=pressures[WHEEL_FR],
        rear_left=pressures[WHEEL_RL],
        rear_right=pressures[WHEEL_RR],
    )


def _map_weather(rf2_data: dict) -> str | None:
    """Map rF2 weather data to a condition string."""
    raining = rf2_data.get("mRaining")
    if raining is None:
        return None
    if raining < 0.1:
        return "dry"
    if raining < 0.5:
        return "mixed"
    return "wet"


def _clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to the given range."""
    return max(min_val, min(max_val, value))
