from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.session import Session


class CarSetup(Base):
    """Persisted car setup (metadata + JSON parameters).

    The ``parameters`` column stores JSON shaped like ``SetupParameters`` in
    ``src.models.schemas``: optional common fields plus arbitrary extra keys for
    title-specific values.
    """

    __tablename__ = "car_setups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    car_name: Mapped[str] = mapped_column(String(255), index=True)
    track_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("sessions.id"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=lambda: {})
    source_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[Session | None] = relationship(back_populates="setups")
