from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.lap import LapSummary
    from src.models.setup import CarSetup
    from src.models.telemetry import TelemetryFrame


class SessionType(enum.StrEnum):
    PRACTICE = "practice"
    QUALIFYING = "qualifying"
    RACE = "race"
    UNKNOWN = "unknown"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    track_name: Mapped[str] = mapped_column(String(255))
    car_name: Mapped[str] = mapped_column(String(255))
    driver_name: Mapped[str] = mapped_column(String(255), default="Player")
    session_type: Mapped[SessionType] = mapped_column(
        SAEnum(SessionType), default=SessionType.UNKNOWN
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_laps: Mapped[int] = mapped_column(Integer, default=0)
    best_lap_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    frames: Mapped[list[TelemetryFrame]] = relationship(back_populates="session")
    laps: Mapped[list[LapSummary]] = relationship(back_populates="session")
    setups: Mapped[list[CarSetup]] = relationship(back_populates="session")
