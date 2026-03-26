"""Unit tests for src/core/lap_analyzer.py — lap boundary detection,
summary computation, and comparison logic.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.core.lap_analyzer import (
    compare_laps,
    compute_lap_summary,
    compute_sector_deltas,
    detect_lap_boundaries,
    detect_sector_boundaries,
)
from src.models.lap import LapSummary
from src.models.telemetry import TelemetryFrame

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _frame(
    *,
    lap_number: int = 1,
    sector: int = 1,
    offset_seconds: float = 0.0,
    speed: float = 200.0,
    throttle: float = 0.8,
    brake: float = 0.0,
    steering: float = 0.0,
    gear: int = 4,
    fuel_level: float = 50.0,
    tire_temps: dict | None = "default",
    session_id: int = 1,
) -> TelemetryFrame:
    """Build a TelemetryFrame with sensible defaults."""
    base_time = datetime(2026, 3, 24, 14, 0, 0, tzinfo=UTC)
    if tire_temps == "default":
        tire_temps = {
            "front_left": 95.0,
            "front_right": 96.0,
            "rear_left": 98.0,
            "rear_right": 97.0,
        }
    return TelemetryFrame(
        session_id=session_id,
        timestamp=base_time + timedelta(seconds=offset_seconds),
        lap_number=lap_number,
        sector=sector,
        throttle=throttle,
        brake=brake,
        steering=steering,
        gear=gear,
        speed=speed,
        rpm=8000.0,
        position_x=0.0,
        position_y=0.0,
        position_z=0.0,
        tire_temps=tire_temps,
        tire_pressures=None,
        fuel_level=fuel_level,
        weather_conditions="dry",
    )


# ---------------------------------------------------------------------------
# Test: detect_lap_boundaries
# ---------------------------------------------------------------------------


class TestDetectLapBoundaries:
    def test_groups_frames_by_lap_number(self):
        frames = [
            _frame(lap_number=1, offset_seconds=0),
            _frame(lap_number=1, offset_seconds=1),
            _frame(lap_number=2, offset_seconds=2),
            _frame(lap_number=2, offset_seconds=3),
            _frame(lap_number=3, offset_seconds=4),
        ]
        laps = detect_lap_boundaries(frames)
        assert set(laps.keys()) == {1, 2, 3}
        assert len(laps[1]) == 2
        assert len(laps[2]) == 2
        assert len(laps[3]) == 1

    def test_sorts_frames_by_timestamp(self):
        frames = [
            _frame(lap_number=1, offset_seconds=2),
            _frame(lap_number=1, offset_seconds=0),
            _frame(lap_number=1, offset_seconds=1),
        ]
        laps = detect_lap_boundaries(frames)
        timestamps = [f.timestamp for f in laps[1]]
        assert timestamps == sorted(timestamps)

    def test_empty_frames(self):
        assert detect_lap_boundaries([]) == {}

    def test_single_lap(self):
        frames = [_frame(lap_number=5, offset_seconds=i) for i in range(10)]
        laps = detect_lap_boundaries(frames)
        assert list(laps.keys()) == [5]
        assert len(laps[5]) == 10


# ---------------------------------------------------------------------------
# Test: detect_sector_boundaries
# ---------------------------------------------------------------------------


class TestDetectSectorBoundaries:
    def test_groups_by_sector(self):
        frames = [
            _frame(sector=1, offset_seconds=0),
            _frame(sector=1, offset_seconds=1),
            _frame(sector=2, offset_seconds=2),
            _frame(sector=2, offset_seconds=3),
            _frame(sector=3, offset_seconds=4),
            _frame(sector=3, offset_seconds=5),
        ]
        sectors = detect_sector_boundaries(frames)
        assert set(sectors.keys()) == {1, 2, 3}
        assert len(sectors[1]) == 2
        assert len(sectors[2]) == 2
        assert len(sectors[3]) == 2


# ---------------------------------------------------------------------------
# Test: compute_lap_summary
# ---------------------------------------------------------------------------


class TestComputeLapSummary:
    def test_basic_lap_summary(self):
        frames = [
            _frame(
                lap_number=1,
                sector=1,
                offset_seconds=0,
                speed=180.0,
                fuel_level=50.0,
            ),
            _frame(
                lap_number=1,
                sector=1,
                offset_seconds=20,
                speed=220.0,
                fuel_level=49.5,
            ),
            _frame(
                lap_number=1,
                sector=2,
                offset_seconds=40,
                speed=250.0,
                fuel_level=49.0,
            ),
            _frame(
                lap_number=1,
                sector=2,
                offset_seconds=60,
                speed=200.0,
                fuel_level=48.5,
            ),
            _frame(
                lap_number=1,
                sector=3,
                offset_seconds=70,
                speed=190.0,
                fuel_level=48.2,
            ),
            _frame(
                lap_number=1,
                sector=3,
                offset_seconds=85,
                speed=210.0,
                fuel_level=47.8,
            ),
        ]
        summary = compute_lap_summary(session_id=1, lap_number=1, frames=frames)

        assert summary is not None
        assert summary.lap_number == 1
        assert summary.lap_time == 85.0
        assert summary.top_speed == 250.0
        assert summary.fuel_used == pytest.approx(2.2, abs=0.01)
        assert summary.fuel_level_start == 50.0
        assert summary.fuel_level_end == 47.8
        assert summary.is_valid is True
        assert summary.is_pit_lap is False

    def test_sector_times_computed(self):
        frames = [
            _frame(sector=1, offset_seconds=0),
            _frame(sector=1, offset_seconds=25),
            _frame(sector=2, offset_seconds=30),
            _frame(sector=2, offset_seconds=55),
            _frame(sector=3, offset_seconds=60),
            _frame(sector=3, offset_seconds=80),
        ]
        summary = compute_lap_summary(1, 1, frames)
        assert summary is not None
        assert summary.sector_1_time == 25.0
        assert summary.sector_2_time == 25.0
        assert summary.sector_3_time == 20.0

    def test_pit_lap_detection(self):
        frames = [
            _frame(offset_seconds=0, speed=200.0, gear=4),
            _frame(offset_seconds=30, speed=20.0, gear=0),  # pit lane
            _frame(offset_seconds=60, speed=15.0, gear=0),
            _frame(offset_seconds=120, speed=180.0, gear=3),
        ]
        summary = compute_lap_summary(1, 1, frames)
        assert summary is not None
        assert summary.is_pit_lap is True
        assert summary.is_valid is False

    def test_too_few_frames_returns_none(self):
        frames = [_frame(offset_seconds=0)]
        assert compute_lap_summary(1, 1, frames) is None

    def test_zero_duration_returns_none(self):
        frames = [
            _frame(offset_seconds=0),
            _frame(offset_seconds=0),
        ]
        assert compute_lap_summary(1, 1, frames) is None

    def test_tire_temps_min_max(self):
        frames = [
            _frame(
                offset_seconds=0,
                tire_temps={
                    "front_left": 80.0,
                    "front_right": 85.0,
                    "rear_left": 90.0,
                    "rear_right": 92.0,
                },
            ),
            _frame(
                offset_seconds=60,
                tire_temps={
                    "front_left": 95.0,
                    "front_right": 100.0,
                    "rear_left": 105.0,
                    "rear_right": 110.0,
                },
            ),
        ]
        summary = compute_lap_summary(1, 1, frames)
        assert summary is not None
        assert summary.min_tire_temp == 80.0
        assert summary.max_tire_temp == 110.0

    def test_no_tire_temps(self):
        frames = [
            _frame(offset_seconds=0, tire_temps=None),
            _frame(offset_seconds=60, tire_temps=None),
        ]
        summary = compute_lap_summary(1, 1, frames)
        assert summary is not None
        assert summary.min_tire_temp is None
        assert summary.max_tire_temp is None

    def test_average_speed(self):
        frames = [
            _frame(offset_seconds=0, speed=100.0),
            _frame(offset_seconds=30, speed=200.0),
            _frame(offset_seconds=60, speed=300.0),
        ]
        summary = compute_lap_summary(1, 1, frames)
        assert summary is not None
        assert summary.average_speed == 200.0

    def test_short_lap_invalid(self):
        """Laps under 10 seconds are marked invalid."""
        frames = [
            _frame(offset_seconds=0, speed=200.0),
            _frame(offset_seconds=5, speed=200.0),
        ]
        summary = compute_lap_summary(1, 1, frames)
        assert summary is not None
        assert summary.is_valid is False


# ---------------------------------------------------------------------------
# Test: compare_laps (trace comparison)
# ---------------------------------------------------------------------------


class TestCompareLaps:
    def test_speed_trace_generation(self):
        lap_a = [
            _frame(offset_seconds=0, speed=100.0),
            _frame(offset_seconds=30, speed=200.0),
            _frame(offset_seconds=60, speed=150.0),
        ]
        lap_b = [
            _frame(offset_seconds=0, speed=120.0),
            _frame(offset_seconds=30, speed=210.0),
            _frame(offset_seconds=60, speed=160.0),
        ]
        speed_trace, input_trace = compare_laps(lap_a, lap_b, sample_points=10)

        assert len(speed_trace) == 11  # 0 through 10 inclusive
        assert len(input_trace) == 11
        # First point should be at offset 0
        assert speed_trace[0]["timestamp_offset"] == 0.0
        # Last point offset should be close to 60s
        assert speed_trace[-1]["timestamp_offset"] == pytest.approx(60.0, abs=0.1)

    def test_empty_laps(self):
        speed_trace, input_trace = compare_laps([], [], 10)
        assert speed_trace == []
        assert input_trace == []

    def test_input_trace_has_throttle_brake(self):
        lap_a = [
            _frame(offset_seconds=0, throttle=0.8, brake=0.0),
            _frame(offset_seconds=30, throttle=0.0, brake=0.9),
        ]
        lap_b = [
            _frame(offset_seconds=0, throttle=0.5, brake=0.1),
            _frame(offset_seconds=30, throttle=0.3, brake=0.6),
        ]
        _, input_trace = compare_laps(lap_a, lap_b, sample_points=5)
        assert len(input_trace) > 0
        point = input_trace[0]
        assert "lap_a_throttle" in point
        assert "lap_a_brake" in point
        assert "lap_b_throttle" in point
        assert "lap_b_brake" in point


# ---------------------------------------------------------------------------
# Test: compute_sector_deltas
# ---------------------------------------------------------------------------


class TestComputeSectorDeltas:
    def test_all_sectors_present(self):
        lap_a = LapSummary(
            session_id=1,
            lap_number=1,
            lap_time=80.0,
            sector_1_time=25.0,
            sector_2_time=30.0,
            sector_3_time=25.0,
            started_at=datetime(2026, 3, 24, 14, 0, 0),
            ended_at=datetime(2026, 3, 24, 14, 1, 20),
        )
        lap_b = LapSummary(
            session_id=1,
            lap_number=2,
            lap_time=78.0,
            sector_1_time=24.0,
            sector_2_time=29.5,
            sector_3_time=24.5,
            started_at=datetime(2026, 3, 24, 14, 1, 20),
            ended_at=datetime(2026, 3, 24, 14, 2, 38),
        )

        deltas = compute_sector_deltas(lap_a, lap_b)
        assert len(deltas) == 3
        assert deltas[0]["sector"] == 1
        assert deltas[0]["delta"] == pytest.approx(-1.0)
        assert deltas[1]["delta"] == pytest.approx(-0.5)
        assert deltas[2]["delta"] == pytest.approx(-0.5)

    def test_missing_sector_times(self):
        lap_a = LapSummary(
            session_id=1,
            lap_number=1,
            lap_time=80.0,
            sector_1_time=25.0,
            sector_2_time=None,
            sector_3_time=25.0,
            started_at=datetime(2026, 3, 24, 14, 0, 0),
            ended_at=datetime(2026, 3, 24, 14, 1, 20),
        )
        lap_b = LapSummary(
            session_id=1,
            lap_number=2,
            lap_time=78.0,
            sector_1_time=24.0,
            sector_2_time=29.0,
            sector_3_time=None,
            started_at=datetime(2026, 3, 24, 14, 1, 20),
            ended_at=datetime(2026, 3, 24, 14, 2, 38),
        )

        deltas = compute_sector_deltas(lap_a, lap_b)
        assert deltas[0]["delta"] == pytest.approx(-1.0)
        assert deltas[1]["delta"] is None  # one side missing
        assert deltas[2]["delta"] is None  # one side missing
