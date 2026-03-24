from datetime import datetime

from src.models.schemas import HealthResponse, TelemetryFrameCreate, TireData


def test_health_response_schema():
    resp = HealthResponse(version="0.1.0", environment="development")
    assert resp.status == "ok"


def test_telemetry_frame_create_minimal():
    frame = TelemetryFrameCreate(
        session_id=1,
        timestamp=datetime.utcnow(),
        lap_number=1,
        throttle=0.5,
        brake=0.0,
        steering=0.1,
        gear=3,
        speed=120.5,
    )
    assert frame.lap_number == 1
    assert frame.tire_temps is None


def test_tire_data_schema():
    tires = TireData(front_left=85.0, front_right=87.0, rear_left=90.0, rear_right=91.0)
    assert tires.front_left == 85.0
