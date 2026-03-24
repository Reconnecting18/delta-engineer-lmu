from datetime import datetime

from pydantic import BaseModel, Field

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
    """Schema for incoming telemetry frames (POST /telemetry — Milestone 2)."""

    session_id: int
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
