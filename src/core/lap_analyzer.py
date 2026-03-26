"""Lap boundary detection, summary computation, and comparison.

Handles:
- Detecting lap boundaries from telemetry frame sequences (#8)
- Computing per-lap statistics (time, sectors, speed, tires, fuel) (#9)
- Comparing two laps with delta analysis (#11)
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.lap import LapSummary
from src.models.telemetry import TelemetryFrame

# ---------------------------------------------------------------------------
# Lap boundary detection (#8)
# ---------------------------------------------------------------------------


def detect_lap_boundaries(
    frames: list[TelemetryFrame],
) -> dict[int, list[TelemetryFrame]]:
    """Group telemetry frames by lap number.

    Frames are assumed to already carry a `lap_number` field set by the
    telemetry source (LMU sector triggers / distance-around-track).

    Returns a dict mapping lap_number → list of frames sorted by timestamp.
    """
    laps: dict[int, list[TelemetryFrame]] = {}
    for frame in frames:
        laps.setdefault(frame.lap_number, []).append(frame)

    # Sort each lap's frames by timestamp
    for lap_frames in laps.values():
        lap_frames.sort(key=lambda f: f.timestamp)

    return laps


def detect_sector_boundaries(
    frames: list[TelemetryFrame],
) -> dict[int, list[TelemetryFrame]]:
    """Group a single lap's frames by sector.

    Returns a dict mapping sector_number → list of frames sorted by timestamp.
    """
    sectors: dict[int, list[TelemetryFrame]] = {}
    for frame in frames:
        sectors.setdefault(frame.sector, []).append(frame)

    for sector_frames in sectors.values():
        sector_frames.sort(key=lambda f: f.timestamp)

    return sectors


# ---------------------------------------------------------------------------
# Lap summary computation (#9)
# ---------------------------------------------------------------------------


def _extract_tire_temps(frame: TelemetryFrame) -> list[float]:
    """Extract all tire temperature values from a frame's JSON tire_temps."""
    if not frame.tire_temps:
        return []
    td = frame.tire_temps
    if isinstance(td, dict):
        return [
            td.get("front_left", 0.0),
            td.get("front_right", 0.0),
            td.get("rear_left", 0.0),
            td.get("rear_right", 0.0),
        ]
    return []


def compute_lap_summary(
    session_id: int,
    lap_number: int,
    frames: list[TelemetryFrame],
) -> LapSummary | None:
    """Compute a LapSummary from a set of telemetry frames for one lap.

    Returns None if there are fewer than 2 frames (can't compute a lap time).
    """
    if len(frames) < 2:
        return None

    # Ensure sorted by timestamp
    sorted_frames = sorted(frames, key=lambda f: f.timestamp)
    first = sorted_frames[0]
    last = sorted_frames[-1]

    # Lap time = time span of the frames
    lap_time = (last.timestamp - first.timestamp).total_seconds()
    if lap_time <= 0:
        return None

    # Sector times
    sectors = detect_sector_boundaries(sorted_frames)
    sector_times: dict[int, float] = {}
    for sector_num, sector_frames in sectors.items():
        if len(sector_frames) >= 2:
            s_first = sector_frames[0]
            s_last = sector_frames[-1]
            sector_times[sector_num] = (
                s_last.timestamp - s_first.timestamp
            ).total_seconds()

    # Speed stats
    speeds = [f.speed for f in sorted_frames]
    top_speed = max(speeds)
    average_speed = sum(speeds) / len(speeds)

    # Tire temps (min/max across all frames and all corners)
    all_temps: list[float] = []
    for f in sorted_frames:
        temps = _extract_tire_temps(f)
        all_temps.extend(t for t in temps if t > 0)

    min_tire_temp = min(all_temps) if all_temps else None
    max_tire_temp = max(all_temps) if all_temps else None

    # Fuel
    fuel_level_start = first.fuel_level
    fuel_level_end = last.fuel_level
    fuel_used = max(0.0, fuel_level_start - fuel_level_end)

    # Validity: detect pit laps by very slow speeds or gear 0 (neutral) periods
    # A lap is a pit lap if the minimum speed is below 30 km/h at any point
    # (typical pit lane speed limit area)
    is_pit_lap = min(speeds) < 30.0 and any(f.gear == 0 for f in sorted_frames)

    # A lap is invalid if it's a pit lap or the lap time is unrealistically short
    is_valid = not is_pit_lap and lap_time > 10.0

    return LapSummary(
        session_id=session_id,
        lap_number=lap_number,
        lap_time=lap_time,
        sector_1_time=sector_times.get(1),
        sector_2_time=sector_times.get(2),
        sector_3_time=sector_times.get(3),
        top_speed=top_speed,
        average_speed=round(average_speed, 2),
        min_tire_temp=min_tire_temp,
        max_tire_temp=max_tire_temp,
        fuel_used=round(fuel_used, 3),
        fuel_level_start=fuel_level_start,
        fuel_level_end=fuel_level_end,
        is_valid=is_valid,
        is_pit_lap=is_pit_lap,
        started_at=first.timestamp,
        ended_at=last.timestamp,
    )


async def compute_and_store_laps(
    session_id: int,
    db: AsyncSession,
) -> list[LapSummary]:
    """Detect lap boundaries and compute summaries for all laps in a session.

    Deletes any existing summaries for the session first (idempotent rebuild).
    Returns the list of newly created LapSummary records.
    """
    # Load all frames for the session
    stmt = (
        select(TelemetryFrame)
        .where(TelemetryFrame.session_id == session_id)
        .order_by(TelemetryFrame.timestamp)
    )
    result = await db.execute(stmt)
    frames = list(result.scalars().all())

    if not frames:
        return []

    # Delete existing summaries for idempotent rebuild
    from sqlalchemy import delete

    await db.execute(delete(LapSummary).where(LapSummary.session_id == session_id))

    # Detect boundaries and compute
    laps_by_number = detect_lap_boundaries(frames)
    summaries: list[LapSummary] = []

    for lap_number, lap_frames in sorted(laps_by_number.items()):
        summary = compute_lap_summary(session_id, lap_number, lap_frames)
        if summary is not None:
            db.add(summary)
            summaries.append(summary)

    await db.flush()
    # Refresh to get IDs
    for s in summaries:
        await db.refresh(s)

    return summaries


# ---------------------------------------------------------------------------
# Lap comparison (#11)
# ---------------------------------------------------------------------------


async def get_lap_frames(
    lap_summary: LapSummary,
    db: AsyncSession,
) -> list[TelemetryFrame]:
    """Load telemetry frames for a specific lap."""
    stmt = (
        select(TelemetryFrame)
        .where(
            TelemetryFrame.session_id == lap_summary.session_id,
            TelemetryFrame.lap_number == lap_summary.lap_number,
        )
        .order_by(TelemetryFrame.timestamp)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _frames_to_offset_series(
    frames: list[TelemetryFrame],
) -> list[tuple[float, TelemetryFrame]]:
    """Convert frames to (offset_seconds, frame) pairs from lap start."""
    if not frames:
        return []
    start = frames[0].timestamp
    return [((f.timestamp - start).total_seconds(), f) for f in frames]


def compare_laps(
    lap_a_frames: list[TelemetryFrame],
    lap_b_frames: list[TelemetryFrame],
    sample_points: int = 100,
) -> tuple[list[dict], list[dict]]:
    """Compare two laps' telemetry, returning speed trace and input trace.

    Both traces are sampled at evenly-spaced time offsets (relative to each
    lap's start) so laps of different lengths can be compared fairly.

    Returns (speed_trace, input_trace) as lists of dicts matching the
    SpeedTracePoint / InputTracePoint schemas.
    """
    series_a = _frames_to_offset_series(lap_a_frames)
    series_b = _frames_to_offset_series(lap_b_frames)

    if not series_a or not series_b:
        return [], []

    max_offset = min(series_a[-1][0], series_b[-1][0])
    if max_offset <= 0:
        return [], []

    step = max_offset / sample_points

    speed_trace: list[dict] = []
    input_trace: list[dict] = []

    idx_a = 0
    idx_b = 0

    for i in range(sample_points + 1):
        t = i * step

        # Advance indices to the closest frame at or before time t
        while idx_a < len(series_a) - 1 and series_a[idx_a + 1][0] <= t:
            idx_a += 1
        while idx_b < len(series_b) - 1 and series_b[idx_b + 1][0] <= t:
            idx_b += 1

        fa = series_a[idx_a][1]
        fb = series_b[idx_b][1]

        speed_trace.append(
            {
                "timestamp_offset": round(t, 3),
                "lap_a_speed": fa.speed,
                "lap_b_speed": fb.speed,
                "speed_delta": round(fb.speed - fa.speed, 2),
            }
        )
        input_trace.append(
            {
                "timestamp_offset": round(t, 3),
                "lap_a_throttle": fa.throttle,
                "lap_a_brake": fa.brake,
                "lap_b_throttle": fb.throttle,
                "lap_b_brake": fb.brake,
            }
        )

    return speed_trace, input_trace


def compute_sector_deltas(
    lap_a: LapSummary,
    lap_b: LapSummary,
) -> list[dict]:
    """Compute sector-by-sector time deltas between two laps."""
    deltas = []
    for sector in (1, 2, 3):
        a_time = getattr(lap_a, f"sector_{sector}_time")
        b_time = getattr(lap_b, f"sector_{sector}_time")
        delta = None
        if a_time is not None and b_time is not None:
            delta = round(b_time - a_time, 4)
        deltas.append(
            {
                "sector": sector,
                "lap_a_time": a_time,
                "lap_b_time": b_time,
                "delta": delta,
            }
        )
    return deltas
