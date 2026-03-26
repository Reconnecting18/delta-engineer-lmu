"""Session management endpoints.

POST /sessions    — Create a new session
GET  /sessions    — List sessions with pagination and filtering
GET  /sessions/id — Get session detail with frame count
PATCH /sessions/id — Update/end a session
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.session_manager import end_session as end_session_logic
from src.core.session_manager import get_session_frame_count
from src.db.engine import get_db
from src.models.schemas import (
    PaginatedResponse,
    SessionCreate,
    SessionDetailResponse,
    SessionResponse,
    SessionUpdate,
)
from src.models.session import Session, SessionType

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    session_in: SessionCreate,
    db: AsyncSession = Depends(get_db),
) -> Session:
    """Create a new telemetry session."""
    try:
        st = SessionType(session_in.session_type)
    except ValueError:
        st = SessionType.UNKNOWN

    session = Session(
        track_name=session_in.track_name,
        car_name=session_in.car_name,
        driver_name=session_in.driver_name,
        session_type=st,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/", response_model=PaginatedResponse[SessionResponse])
async def list_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session_type: str | None = None,
    track_name: str | None = None,
    car_name: str | None = None,
    driver_name: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List sessions with pagination and optional filters."""
    stmt = select(Session)
    count_stmt = select(func.count()).select_from(Session)

    # Apply filters
    if session_type:
        try:
            st = SessionType(session_type)
            stmt = stmt.where(Session.session_type == st)
            count_stmt = count_stmt.where(Session.session_type == st)
        except ValueError:
            pass

    if track_name:
        stmt = stmt.where(Session.track_name == track_name)
        count_stmt = count_stmt.where(Session.track_name == track_name)

    if car_name:
        stmt = stmt.where(Session.car_name == car_name)
        count_stmt = count_stmt.where(Session.car_name == car_name)

    if driver_name:
        stmt = stmt.where(Session.driver_name == driver_name)
        count_stmt = count_stmt.where(Session.driver_name == driver_name)

    # Get total count
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Apply pagination
    stmt = stmt.order_by(Session.started_at.desc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": PaginatedResponse.compute_pages(total, limit),
    }


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get session detail with frame count."""
    stmt = select(Session).where(Session.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    frame_count = await get_session_frame_count(session_id, db)

    duration_seconds = None
    if session.ended_at and session.started_at:
        duration_seconds = (session.ended_at - session.started_at).total_seconds()

    return {
        "id": session.id,
        "track_name": session.track_name,
        "car_name": session.car_name,
        "driver_name": session.driver_name,
        "session_type": session.session_type.value,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "total_laps": session.total_laps,
        "best_lap_time": session.best_lap_time,
        "frame_count": frame_count,
        "duration_seconds": duration_seconds,
    }


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    update: SessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> Session:
    """Update or end a session."""
    stmt = select(Session).where(Session.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if update.ended_at is not None:
        await end_session_logic(session, db)
    if update.total_laps is not None:
        session.total_laps = update.total_laps
    if update.best_lap_time is not None:
        session.best_lap_time = update.best_lap_time

    await db.commit()
    await db.refresh(session)
    return session
