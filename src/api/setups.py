"""Car setup library endpoints.

POST /setups — Store a named setup (parameters + metadata)
GET  /setups — List setups with pagination and filtering
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_db
from src.models.schemas import PaginatedResponse, SetupCreate, SetupResponse
from src.models.session import Session
from src.models.setup import CarSetup

router = APIRouter(prefix="/setups", tags=["setups"])


@router.post("/", response_model=SetupResponse, status_code=201)
async def create_setup(
    body: SetupCreate,
    db: AsyncSession = Depends(get_db),
) -> CarSetup:
    """Persist a car setup for later correlation with telemetry."""
    if body.session_id is not None:
        stmt = select(Session).where(Session.id == body.session_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Session not found")

    setup = CarSetup(
        name=body.name,
        car_name=body.car_name,
        track_name=body.track_name,
        session_id=body.session_id,
        notes=body.notes,
        parameters=dict(body.parameters),
        source_filename=body.source_filename,
    )
    db.add(setup)
    await db.commit()
    await db.refresh(setup)
    return setup


@router.get("/", response_model=PaginatedResponse[SetupResponse])
async def list_setups(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    car_name: str | None = None,
    track_name: str | None = None,
    session_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List setups with optional filters (car, track, linked session)."""
    stmt = select(CarSetup)
    count_stmt = select(func.count()).select_from(CarSetup)

    if car_name is not None:
        stmt = stmt.where(CarSetup.car_name == car_name)
        count_stmt = count_stmt.where(CarSetup.car_name == car_name)

    if track_name is not None:
        stmt = stmt.where(CarSetup.track_name == track_name)
        count_stmt = count_stmt.where(CarSetup.track_name == track_name)

    if session_id is not None:
        stmt = stmt.where(CarSetup.session_id == session_id)
        count_stmt = count_stmt.where(CarSetup.session_id == session_id)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(CarSetup.created_at.desc())
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
