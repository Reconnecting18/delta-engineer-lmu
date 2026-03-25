from __future__ import annotations

import math
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")

# --- Health ---


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str


# --- Tire data ---


class TireData(BaseModel):
    front_left: float
    front_right: float
    rear_left: float
    rear_right: float


# --- Telemetry ---


class TelemetryFrameCreate(BaseModel):
    """Schema for incoming telemetry frames (POST /telemetry).

    session_id is optional here — it's typically provided at the request level
    (TelemetryIngestRequest) and set by the endpoint before persisting.
    """

    session_id: int | None = None
    timestamp: datetime
    lap_number: int
    sector: int = 0
    throttle: float = Field(ge=0.0, le=1.0)
    brake: float = Field(ge=0.0, le=1.0)
    steering: float = Field(ge=-1.0, le=1.0)
    gear: int
    speed: float
    rpm: float = 0.0
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    tire_temps: TireData | None = None
    tire_pressures: TireData | None = None
    fuel_level: float = 0.0
    weather_conditions: str | None = None


class TelemetryFrameResponse(TelemetryFrameCreate):
    id: int

    model_config = {"from_attributes": True}


# --- Session ---


class SessionCreate(BaseModel):
    track_name: str
    car_name: str
    driver_name: str = "Player"
    session_type: str = "unknown"


class SessionResponse(BaseModel):
    id: int
    track_name: str
    car_name: str
    driver_name: str
    session_type: str
    started_at: datetime
    ended_at: datetime | None
    total_laps: int
    best_lap_time: float | None

    model_config = {"from_attributes": True}


class SessionUpdate(BaseModel):
    """For ending/updating a session."""

    ended_at: datetime | None = None
    total_laps: int | None = None
    best_lap_time: float | None = None


class SessionDetailResponse(SessionResponse):
    """Session with computed stats."""

    frame_count: int = 0
    duration_seconds: float | None = None


# --- Pagination ---


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic pagination wrapper."""

    items: list[T]
    total: int
    page: int
    limit: int
    pages: int

    @staticmethod
    def compute_pages(total: int, limit: int) -> int:
        return max(1, math.ceil(total / limit)) if total > 0 else 0


# --- Telemetry Ingestion ---


class FrameError(BaseModel):
    """Error detail for a single frame that failed validation/parsing."""

    index: int
    error: str


class TelemetryIngestRequest(BaseModel):
    """Flexible ingestion payload supporting single and batch frames."""

    session_id: int | None = None
    frames: list[TelemetryFrameCreate] = []
    raw_data: str | None = None
    format: str = "json"

    # Context fields for session auto-detection when session_id not provided
    track_name: str | None = None
    car_name: str | None = None
    driver_name: str | None = None
    session_type: str | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> TelemetryIngestRequest:
        if not self.frames and not self.raw_data:
            raise ValueError("Either 'frames' or 'raw_data' must be provided")
        if self.frames and self.raw_data:
            raise ValueError("Provide 'frames' or 'raw_data', not both")
        return self


class TelemetryIngestResponse(BaseModel):
    """Receipt returned after ingestion."""

    session_id: int
    frames_received: int
    frames_stored: int
    frames_failed: int
    errors: list[FrameError]
    timestamp: datetime
