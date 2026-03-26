"""Lap analysis endpoints.

GET  /sessions/{id}/laps   — List lap summaries for a session (#10)
GET  /laps/compare          — Compare two or more laps (#11)
POST /sessions/{id}/laps/compute — Trigger lap computation for a session
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.lap_analyzer import (
    compare_laps,
    compute_and_store_laps,
    compute_sector_deltas,
    get_lap_frames,
)
from src.db.engine import get_db
from src.models.lap import LapSummary
from src.models.schemas import (
    LapComparisonResult,
    LapSummaryResponse,
    PaginatedResponse,
)
from src.models.session import Session

router = APIRouter(tags=["laps"])


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/laps (#10)
# ---------------------------------------------------------------------------


@router.get(
    "/sessions/{session_id}/laps",
    response_model=PaginatedResponse[LapSummaryResponse],
)
async def list_session_laps(
    session_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    valid_only: bool = Query(False),
    sort_by: str = Query("lap_number", pattern="^(lap_number|lap_time)$"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return all lap summaries for a session.

    Supports filtering by validity and sorting by lap_number or lap_time.
    """
    # Verify session exists
    sess_result = await db.execute(select(Session).where(Session.id == session_id))
    if sess_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build query
    stmt = select(LapSummary).where(LapSummary.session_id == session_id)
    count_stmt = (
        select(func.count())
        .select_from(LapSummary)
        .where(LapSummary.session_id == session_id)
    )

    if valid_only:
        stmt = stmt.where(LapSummary.is_valid.is_(True))
        count_stmt = count_stmt.where(LapSummary.is_valid.is_(True))

    # Sort
    order_col = LapSummary.lap_time if sort_by == "lap_time" else LapSummary.lap_number
    stmt = stmt.order_by(order_col)

    # Total count
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginate
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


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/laps/compute
# ---------------------------------------------------------------------------


@router.post(
    "/sessions/{session_id}/laps/compute",
    response_model=list[LapSummaryResponse],
    status_code=201,
)
async def compute_session_laps(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[LapSummary]:
    """Trigger lap boundary detection and summary computation for a session.

    This is idempotent — existing summaries are rebuilt from telemetry frames.
    """
    # Verify session exists
    sess_result = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    summaries = await compute_and_store_laps(session_id, db)

    # Update session best_lap_time
    valid_laps = [s for s in summaries if s.is_valid]
    if valid_laps:
        best = min(valid_laps, key=lambda s: s.lap_time)
        session.best_lap_time = best.lap_time

    await db.commit()
    return summaries


# ---------------------------------------------------------------------------
# GET /laps/compare (#11)
# ---------------------------------------------------------------------------


@router.get("/laps/compare", response_model=LapComparisonResult)
async def compare_laps_endpoint(
    ids: str = Query(..., description="Comma-separated lap summary IDs (exactly 2)"),
    sample_points: int = Query(100, ge=10, le=500),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Compare two laps with full delta analysis.

    Returns sector-by-sector time deltas, speed trace comparison,
    and throttle/brake input comparison.
    """
    try:
        lap_ids = [int(x.strip()) for x in ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="ids must be comma-separated integers",
        )

    if len(lap_ids) != 2:
        raise HTTPException(
            status_code=400, detail="Exactly 2 lap IDs required for comparison"
        )

    # Load both lap summaries
    stmt = select(LapSummary).where(LapSummary.id.in_(lap_ids))
    result = await db.execute(stmt)
    laps = {lap.id: lap for lap in result.scalars().all()}

    for lid in lap_ids:
        if lid not in laps:
            raise HTTPException(status_code=404, detail=f"Lap summary {lid} not found")

    lap_a = laps[lap_ids[0]]
    lap_b = laps[lap_ids[1]]

    # Load frames for both laps
    frames_a = await get_lap_frames(lap_a, db)
    frames_b = await get_lap_frames(lap_b, db)

    # Compute deltas
    sector_deltas = compute_sector_deltas(lap_a, lap_b)
    speed_trace, input_trace = compare_laps(frames_a, frames_b, sample_points)

    return {
        "lap_a": lap_a,
        "lap_b": lap_b,
        "time_delta": round(lap_b.lap_time - lap_a.lap_time, 4),
        "sector_deltas": sector_deltas,
        "speed_trace": speed_trace,
        "input_trace": input_trace,
    }
