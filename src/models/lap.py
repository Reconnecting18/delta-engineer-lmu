from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.session import Session


class LapSummary(Base):
    __tablename__ = "lap_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    lap_number: Mapped[int] = mapped_column(Integer)

    # Timing
    lap_time: Mapped[float] = mapped_column(Float)  # seconds
    sector_1_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector_2_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector_3_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Speed
    top_speed: Mapped[float] = mapped_column(Float, default=0.0)  # km/h
    average_speed: Mapped[float] = mapped_column(Float, default=0.0)  # km/h

    # Tire temps (min/max across all four corners)
    min_tire_temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_tire_temp: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Fuel
    fuel_used: Mapped[float] = mapped_column(Float, default=0.0)  # litres
    fuel_level_start: Mapped[float] = mapped_column(Float, default=0.0)
    fuel_level_end: Mapped[float] = mapped_column(Float, default=0.0)

    # Validity
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pit_lap: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime] = mapped_column(DateTime)

    session: Mapped[Session] = relationship(back_populates="laps")
