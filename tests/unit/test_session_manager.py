"""Unit tests for session boundary detection and management."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.session_manager import (
    end_session,
    get_active_session,
    get_or_create_session,
    get_session_frame_count,
)
from src.models.session import Session, SessionType
from src.models.telemetry import TelemetryFrame
from tests.conftest import test_session_factory


@pytest.fixture
async def db() -> AsyncSession:
    async with test_session_factory() as session:
        yield session


class TestGetOrCreateSession:
    async def test_creates_new_when_none_exists(self, db):
        session = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "practice", db
        )
        assert session.id is not None
        assert session.track_name == "Monza"
        assert session.car_name == "Ferrari 499P"
        assert session.session_type == SessionType.PRACTICE
        assert session.ended_at is None

    async def test_returns_existing_active_session(self, db):
        s1 = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "practice", db
        )
        s2 = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "practice", db
        )
        assert s1.id == s2.id

    async def test_creates_new_on_session_type_change(self, db):
        s1 = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "practice", db
        )
        s2 = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "qualifying", db
        )
        assert s1.id != s2.id

        # Old session should be ended
        await db.refresh(s1)
        assert s1.ended_at is not None

    async def test_creates_new_after_time_gap(self, db):
        s1 = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "practice", db
        )

        # Add a frame with a timestamp
        frame = TelemetryFrame(
            session_id=s1.id,
            timestamp=datetime(2026, 3, 24, 14, 0, 0, tzinfo=UTC),
            lap_number=1,
            sector=0,
            throttle=0.5,
            brake=0.0,
            steering=0.0,
            gear=3,
            speed=200.0,
        )
        db.add(frame)
        await db.flush()

        # Request with a timestamp well past the gap threshold (>300s)
        future_ts = datetime(2026, 3, 24, 14, 10, 0, tzinfo=UTC)
        s2 = await get_or_create_session(
            "Monza",
            "Ferrari 499P",
            "Player",
            "practice",
            db,
            latest_frame_timestamp=future_ts,
        )
        assert s1.id != s2.id

    async def test_reuses_session_within_gap(self, db):
        s1 = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "practice", db
        )

        frame = TelemetryFrame(
            session_id=s1.id,
            timestamp=datetime(2026, 3, 24, 14, 0, 0, tzinfo=UTC),
            lap_number=1,
            sector=0,
            throttle=0.5,
            brake=0.0,
            steering=0.0,
            gear=3,
            speed=200.0,
        )
        db.add(frame)
        await db.flush()

        # Within gap threshold (<300s)
        near_ts = datetime(2026, 3, 24, 14, 2, 0, tzinfo=UTC)
        s2 = await get_or_create_session(
            "Monza",
            "Ferrari 499P",
            "Player",
            "practice",
            db,
            latest_frame_timestamp=near_ts,
        )
        assert s1.id == s2.id

    async def test_unknown_type_does_not_trigger_change(self, db):
        """If incoming type is 'unknown', don't treat it as a change."""
        s1 = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "practice", db
        )
        s2 = await get_or_create_session(
            "Monza", "Ferrari 499P", "Player", "unknown", db
        )
        assert s1.id == s2.id


class TestEndSession:
    async def test_sets_ended_at(self, db):
        s = Session(
            track_name="Monza",
            car_name="Ferrari 499P",
            session_type=SessionType.PRACTICE,
        )
        db.add(s)
        await db.flush()

        await end_session(s, db)
        assert s.ended_at is not None

    async def test_computes_total_laps(self, db):
        s = Session(
            track_name="Monza",
            car_name="Ferrari 499P",
            session_type=SessionType.PRACTICE,
        )
        db.add(s)
        await db.flush()

        for lap in range(1, 4):
            frame = TelemetryFrame(
                session_id=s.id,
                timestamp=datetime.now(UTC),
                lap_number=lap,
                sector=0,
                throttle=0.5,
                brake=0.0,
                steering=0.0,
                gear=3,
                speed=200.0,
            )
            db.add(frame)
        await db.flush()

        await end_session(s, db)
        assert s.total_laps == 3


class TestGetSessionFrameCount:
    async def test_zero_frames(self, db):
        s = Session(
            track_name="Monza",
            car_name="Ferrari 499P",
            session_type=SessionType.PRACTICE,
        )
        db.add(s)
        await db.flush()

        count = await get_session_frame_count(s.id, db)
        assert count == 0

    async def test_counts_frames(self, db):
        s = Session(
            track_name="Monza",
            car_name="Ferrari 499P",
            session_type=SessionType.PRACTICE,
        )
        db.add(s)
        await db.flush()

        for i in range(5):
            frame = TelemetryFrame(
                session_id=s.id,
                timestamp=datetime.now(UTC),
                lap_number=1,
                sector=0,
                throttle=0.5,
                brake=0.0,
                steering=0.0,
                gear=3,
                speed=200.0,
            )
            db.add(frame)
        await db.flush()

        count = await get_session_frame_count(s.id, db)
        assert count == 5
