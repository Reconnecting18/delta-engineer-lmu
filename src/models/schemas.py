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


# --- Lap Summary ---


class LapSummaryResponse(BaseModel):
    id: int
    session_id: int
    lap_number: int
    lap_time: float
    sector_1_time: float | None
    sector_2_time: float | None
    sector_3_time: float | None
    top_speed: float
    average_speed: float
    min_tire_temp: float | None
    max_tire_temp: float | None
    fuel_used: float
    fuel_level_start: float
    fuel_level_end: float
    is_valid: bool
    is_pit_lap: bool
    started_at: datetime
    ended_at: datetime

    model_config = {"from_attributes": True}


# --- Lap Comparison ---


class SectorDelta(BaseModel):
    """Sector-by-sector delta between two laps."""

    sector: int
    lap_a_time: float | None
    lap_b_time: float | None
    delta: float | None  # b - a (negative = b faster)


class SpeedTracePoint(BaseModel):
    """A point on the speed trace for comparison."""

    timestamp_offset: float  # seconds from lap start
    lap_a_speed: float
    lap_b_speed: float
    speed_delta: float  # b - a


class InputTracePoint(BaseModel):
    """Throttle/brake comparison at a point in time."""

    timestamp_offset: float
    lap_a_throttle: float
    lap_a_brake: float
    lap_b_throttle: float
    lap_b_brake: float


class LapComparisonResult(BaseModel):
    """Full delta analysis between two laps."""

    lap_a: LapSummaryResponse
    lap_b: LapSummaryResponse
    time_delta: float  # b - a total lap time
    sector_deltas: list[SectorDelta]
    speed_trace: list[SpeedTracePoint]
    input_trace: list[InputTracePoint]


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


# --- Car setup ---


class SetupCreate(BaseModel):
    """Payload for POST /setups."""

    name: str = Field(min_length=1, max_length=255)
    car_name: str = Field(min_length=1, max_length=255)
    track_name: str | None = Field(default=None, max_length=255)
    session_id: int | None = None
    notes: str | None = None
    parameters: dict[str, object] = Field(default_factory=dict)
    source_filename: str | None = Field(default=None, max_length=512)


class SetupResponse(BaseModel):
    id: int
    name: str
    car_name: str
    track_name: str | None
    session_id: int | None
    notes: str | None
    parameters: dict[str, object]
    source_filename: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
