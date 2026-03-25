"""Session boundary detection and lifecycle management.

Handles auto-detection of session boundaries based on time gaps,
track/car/driver changes, and session type transitions.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.session import Session, SessionType
from src.models.telemetry import TelemetryFrame


async def get_or_create_session(
    track_name: str,
    car_name: str,
    driver_name: str,
    session_type: str,
    db: AsyncSession,
    latest_frame_timestamp: datetime | None = None,
) -> Session:
    """Find the active session for the given context, or create a new one.

    Session boundary detection rules:
    1. No active session → create new
    2. Time gap > threshold → end old, create new
    3. Session type changed → end old, create new
    4. Otherwise → return existing
    """
    settings = get_settings()

    active = await get_active_session(track_name, car_name, driver_name, db)

    if active is None:
        return await _create_session(
            track_name, car_name, driver_name, session_type, db
        )

    # Check time gap
    if latest_frame_timestamp:
        latest_frame = await _get_latest_frame_timestamp(active.id, db)
        if latest_frame is not None:
            # Normalize both to naive UTC for comparison (SQLite stores naive)
            ts = latest_frame_timestamp.replace(tzinfo=None) if latest_frame_timestamp.tzinfo else latest_frame_timestamp
            lf = latest_frame.replace(tzinfo=None) if latest_frame.tzinfo else latest_frame
            gap = (ts - lf).total_seconds()
            if gap > settings.session_gap_threshold_seconds:
                await end_session(active, db)
                return await _create_session(
                    track_name, car_name, driver_name, session_type, db
                )

    # Check session type change
    if session_type != "unknown" and active.session_type.value != session_type:
        await end_session(active, db)
        return await _create_session(
            track_name, car_name, driver_name, session_type, db
        )

    return active


async def get_active_session(
    track_name: str,
    car_name: str,
    driver_name: str,
    db: AsyncSession,
) -> Session | None:
    """Find the most recent active (not ended) session matching context."""
    stmt = (
        select(Session)
        .where(
            Session.track_name == track_name,
            Session.car_name == car_name,
            Session.driver_name == driver_name,
            Session.ended_at.is_(None),
        )
        .order_by(Session.started_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def end_session(session: Session, db: AsyncSession) -> Session:
    """Mark a session as ended and compute summary stats."""
    session.ended_at = datetime.now(UTC)

    # Compute total laps and best lap time from frames
    stats = await _compute_session_stats(session.id, db)
    session.total_laps = stats["total_laps"]
    if stats["best_lap_time"] is not None:
        session.best_lap_time = stats["best_lap_time"]

    await db.flush()
    return session


async def get_session_frame_count(session_id: int, db: AsyncSession) -> int:
    """Get the number of telemetry frames for a session."""
    stmt = select(func.count()).where(TelemetryFrame.session_id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one()


# --- Private helpers ---


async def _create_session(
    track_name: str,
    car_name: str,
    driver_name: str,
    session_type: str,
    db: AsyncSession,
) -> Session:
    """Create and persist a new session."""
    try:
        st = SessionType(session_type)
    except ValueError:
        st = SessionType.UNKNOWN

    session = Session(
        track_name=track_name,
        car_name=car_name,
        driver_name=driver_name,
        session_type=st,
        started_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def _get_latest_frame_timestamp(
    session_id: int, db: AsyncSession
) -> datetime | None:
    """Get the timestamp of the most recent frame in a session."""
    stmt = (
        select(TelemetryFrame.timestamp)
        .where(TelemetryFrame.session_id == session_id)
        .order_by(TelemetryFrame.timestamp.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _compute_session_stats(
    session_id: int, db: AsyncSession
) -> dict:
    """Compute summary stats for a session from its frames."""
    # Get max lap number
    lap_stmt = select(func.max(TelemetryFrame.lap_number)).where(
        TelemetryFrame.session_id == session_id
    )
    lap_result = await db.execute(lap_stmt)
    max_lap = lap_result.scalar_one_or_none()

    return {
        "total_laps": max_lap or 0,
        "best_lap_time": None,  # Computed in Milestone 3 (lap analysis)
    }
