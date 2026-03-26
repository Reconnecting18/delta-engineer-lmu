"""Integration tests for the telemetry ingestion endpoint."""

from __future__ import annotations

import pytest


@pytest.fixture
async def created_session(client, sample_session_data) -> dict:
    """Create a session and return its response data."""
    resp = await client.post("/sessions/", json=sample_session_data)
    return resp.json()


class TestIngestTelemetry:
    async def test_ingest_single_frame(
        self, client, created_session, sample_frame_data
    ):
        payload = {
            "session_id": created_session["id"],
            "frames": [sample_frame_data],
        }
        resp = await client.post("/telemetry/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["frames_received"] == 1
        assert data["frames_stored"] == 1
        assert data["frames_failed"] == 0
        assert data["session_id"] == created_session["id"]

    async def test_ingest_batch(self, client, created_session, sample_frame_data):
        frames = []
        for i in range(5):
            frame = sample_frame_data.copy()
            frame["timestamp"] = f"2026-03-24T14:30:{i:02d}Z"
            frames.append(frame)

        payload = {
            "session_id": created_session["id"],
            "frames": frames,
        }
        resp = await client.post("/telemetry/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["frames_received"] == 5
        assert data["frames_stored"] == 5

    async def test_ingest_updates_session_laps(
        self, client, created_session, sample_frame_data
    ):
        frame = sample_frame_data.copy()
        frame["lap_number"] = 7

        payload = {
            "session_id": created_session["id"],
            "frames": [frame],
        }
        await client.post("/telemetry/", json=payload)

        # Check session was updated
        resp = await client.get(f"/sessions/{created_session['id']}")
        data = resp.json()
        assert data["total_laps"] == 7
        assert data["frame_count"] == 1

    async def test_ingest_nonexistent_session_returns_404(
        self, client, sample_frame_data
    ):
        payload = {
            "session_id": 99999,
            "frames": [sample_frame_data],
        }
        resp = await client.post("/telemetry/", json=payload)
        assert resp.status_code == 404

    async def test_ingest_no_frames_or_raw_data_returns_422(self, client):
        payload = {"session_id": 1}
        resp = await client.post("/telemetry/", json=payload)
        assert resp.status_code == 422

    async def test_ingest_both_frames_and_raw_data_returns_422(
        self, client, sample_frame_data
    ):
        payload = {
            "session_id": 1,
            "frames": [sample_frame_data],
            "raw_data": "AAAA",
        }
        resp = await client.post("/telemetry/", json=payload)
        assert resp.status_code == 422

    async def test_ingest_with_auto_session_detection(self, client, sample_frame_data):
        """When no session_id, auto-create from track/car/driver context."""
        payload = {
            "frames": [sample_frame_data],
            "track_name": "Monza",
            "car_name": "Ferrari 499P",
            "driver_name": "Test Driver",
            "session_type": "practice",
        }
        resp = await client.post("/telemetry/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["session_id"] is not None
        assert data["frames_stored"] == 1

        # Session should exist
        session_resp = await client.get(f"/sessions/{data['session_id']}")
        assert session_resp.status_code == 200
        session_data = session_resp.json()
        assert session_data["track_name"] == "Monza"
        assert session_data["car_name"] == "Ferrari 499P"

    async def test_ingest_auto_detect_requires_track_and_car(
        self, client, sample_frame_data
    ):
        payload = {
            "frames": [sample_frame_data],
            "driver_name": "Player",
        }
        resp = await client.post("/telemetry/", json=payload)
        assert resp.status_code == 400

    async def test_ingest_auto_detect_reuses_session(self, client, sample_frame_data):
        """Consecutive ingestions with same context reuse the same session."""
        payload = {
            "frames": [sample_frame_data],
            "track_name": "Spa",
            "car_name": "Porsche 963",
        }
        resp1 = await client.post("/telemetry/", json=payload)
        resp2 = await client.post("/telemetry/", json=payload)
        assert resp1.json()["session_id"] == resp2.json()["session_id"]

    async def test_ingest_invalid_frame_data(self, client, created_session):
        """Frame with throttle > 1.0 should fail validation."""
        payload = {
            "session_id": created_session["id"],
            "frames": [
                {
                    "timestamp": "2026-03-24T14:30:00Z",
                    "lap_number": 1,
                    "throttle": 1.5,  # Invalid
                    "brake": 0.0,
                    "steering": 0.0,
                    "gear": 3,
                    "speed": 200.0,
                }
            ],
        }
        resp = await client.post("/telemetry/", json=payload)
        # Pydantic validation catches this at the request level
        assert resp.status_code == 422
