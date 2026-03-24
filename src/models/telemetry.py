from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.session import Session


class TelemetryFrame(Base):
    __tablename__ = "telemetry_frames"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    lap_number: Mapped[int] = mapped_column(Integer)
    sector: Mapped[int] = mapped_column(Integer, default=0)

    # Driver inputs
    throttle: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0
    brake: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0
    steering: Mapped[float] = mapped_column(Float)  # -1.0 to 1.0
    gear: Mapped[int] = mapped_column(Integer)

    # Vehicle state
    speed: Mapped[float] = mapped_column(Float)  # km/h
    rpm: Mapped[float] = mapped_column(Float, default=0.0)
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)

    # Tires — JSON arrays: [FL, FR, RL, RR]
    tire_temps: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tire_pressures: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Fuel
    fuel_level: Mapped[float] = mapped_column(Float, default=0.0)

    # Weather
    weather_conditions: Mapped[str | None] = mapped_column(String(50), nullable=True)

    session: Mapped[Session] = relationship(back_populates="frames")
