"""Telemetry ingestion endpoint.

POST /telemetry — Accept single or batch telemetry frames, persist to storage.
Supports pre-parsed JSON frames and raw binary (base64-encoded) data.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.parser import TelemetryParseError, parse_telemetry_batch
from src.core.session_manager import get_or_create_session
from src.db.engine import get_db
from src.models.schemas import (
    FrameError,
    TelemetryFrameCreate,
    TelemetryIngestRequest,
    TelemetryIngestResponse,
)
from src.models.session import Session
from src.models.telemetry import TelemetryFrame

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/", response_model=TelemetryIngestResponse, status_code=201)
async def ingest_telemetry(
    payload: TelemetryIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> TelemetryIngestResponse:
    """Accept single or batch telemetry frames.

    Supports two modes:
    1. Pre-parsed JSON frames (from Electron client) via `frames`
    2. Raw binary data (base64) via `raw_data` with format="rf2_binary"

    Returns a receipt with frame count, session info, and any errors.
    """
    settings = get_settings()
    frames: list[TelemetryFrameCreate] = []
    errors: list[FrameError] = []

    # --- Step 1: Resolve frames ---
    if payload.raw_data:
        try:
            raw_bytes = base64.b64decode(payload.raw_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 in raw_data")

        try:
            frames = parse_telemetry_batch(raw_bytes)
        except TelemetryParseError as e:
            if e.partial_results:
                frames = e.partial_results
                errors.append(FrameError(index=-1, error=e.message))
            else:
                raise HTTPException(status_code=400, detail=e.message)
    else:
        frames = payload.frames

    # --- Step 2: Enforce max batch size ---
    if len(frames) > settings.max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch exceeds max size ({settings.max_batch_size})",
        )

    frames_received = len(frames)

    # --- Step 3: Resolve session ---
    session = await _resolve_session(payload, frames, db)

    # --- Step 4: Persist frames in batches ---
    stored, persist_errors = await _persist_frames(
        frames, session.id, db, settings.telemetry_batch_size
    )
    errors.extend(persist_errors)

    # --- Step 5: Update session stats ---
    await _update_session_stats(session, frames, db)

    await db.commit()

    return TelemetryIngestResponse(
        session_id=session.id,
        frames_received=frames_received,
        frames_stored=stored,
        frames_failed=len(errors),
        errors=errors,
        timestamp=datetime.now(UTC),
    )


async def _resolve_session(
    payload: TelemetryIngestRequest,
    frames: list[TelemetryFrameCreate],
    db: AsyncSession,
) -> Session:
    """Resolve the target session — explicit ID or auto-detect."""
    if payload.session_id is not None:
        from sqlalchemy import select

        stmt = select(Session).where(Session.id == payload.session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session {payload.session_id} not found",
            )
        return session

    # Auto-detect: need track/car/driver context
    track = payload.track_name
    car = payload.car_name
    driver = payload.driver_name or "Player"
    session_type = payload.session_type or "unknown"

    if not track or not car:
        raise HTTPException(
            status_code=400,
            detail="Either session_id or track_name + car_name must be provided",
        )

    # Use the latest frame timestamp for gap detection
    latest_ts = None
    if frames:
        latest_ts = max(f.timestamp for f in frames)

    return await get_or_create_session(
        track, car, driver, session_type, db, latest_frame_timestamp=latest_ts
    )


async def _persist_frames(
    frames: list[TelemetryFrameCreate],
    session_id: int,
    db: AsyncSession,
    batch_size: int,
) -> tuple[int, list[FrameError]]:
    """Persist frames in batches. Returns (stored_count, errors)."""
    stored = 0
    errors: list[FrameError] = []

    for i in range(0, len(frames), batch_size):
        batch = frames[i : i + batch_size]
        models = []
        for j, frame in enumerate(batch):
            try:
                data = frame.model_dump(exclude={"session_id"})
                # Convert TireData to dict for JSON column
                if data.get("tire_temps"):
                    data["tire_temps"] = data["tire_temps"]
                if data.get("tire_pressures"):
                    data["tire_pressures"] = data["tire_pressures"]

                model = TelemetryFrame(session_id=session_id, **data)
                models.append(model)
            except Exception as e:
                errors.append(FrameError(index=i + j, error=str(e)))

        if models:
            db.add_all(models)
            await db.flush()
            stored += len(models)

    return stored, errors


async def _update_session_stats(
    session: Session,
    frames: list[TelemetryFrameCreate],
    db: AsyncSession,
) -> None:
    """Update session lap count from ingested frames."""
    if not frames:
        return

    max_lap = max(f.lap_number for f in frames)
    if max_lap > session.total_laps:
        session.total_laps = max_lap
        await db.flush()
