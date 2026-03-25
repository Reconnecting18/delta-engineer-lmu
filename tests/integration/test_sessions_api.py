"""Integration tests for session management endpoints."""

from __future__ import annotations

import pytest


class TestCreateSession:
    async def test_create_session_returns_201(self, client, sample_session_data):
        resp = await client.post("/sessions/", json=sample_session_data)
        assert resp.status_code == 201

    async def test_create_session_response_body(self, client, sample_session_data):
        resp = await client.post("/sessions/", json=sample_session_data)
        data = resp.json()
        assert data["track_name"] == "Le Mans 24h Circuit"
        assert data["car_name"] == "Toyota GR010 Hybrid"
        assert data["driver_name"] == "Test Driver"
        assert data["session_type"] == "practice"
        assert data["id"] is not None
        assert data["total_laps"] == 0
        assert data["best_lap_time"] is None
        assert data["ended_at"] is None

    async def test_create_session_defaults(self, client):
        resp = await client.post(
            "/sessions/",
            json={"track_name": "Monza", "car_name": "Ferrari 499P"},
        )
        data = resp.json()
        assert data["driver_name"] == "Player"
        assert data["session_type"] == "unknown"

    async def test_create_session_invalid_type_defaults_unknown(self, client):
        resp = await client.post(
            "/sessions/",
            json={
                "track_name": "Spa",
                "car_name": "Porsche 963",
                "session_type": "not_a_type",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["session_type"] == "unknown"


class TestListSessions:
    async def test_list_empty(self, client):
        resp = await client.get("/sessions/")
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["pages"] == 0

    async def test_list_returns_sessions(self, client, sample_session_data):
        await client.post("/sessions/", json=sample_session_data)
        await client.post("/sessions/", json=sample_session_data)

        resp = await client.get("/sessions/")
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_list_pagination(self, client, sample_session_data):
        for _ in range(5):
            await client.post("/sessions/", json=sample_session_data)

        resp = await client.get("/sessions/?page=1&limit=2")
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 2
        assert data["pages"] == 3

    async def test_filter_by_track(self, client):
        await client.post(
            "/sessions/",
            json={"track_name": "Monza", "car_name": "Car A"},
        )
        await client.post(
            "/sessions/",
            json={"track_name": "Spa", "car_name": "Car B"},
        )

        resp = await client.get("/sessions/?track_name=Monza")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["track_name"] == "Monza"

    async def test_filter_by_session_type(self, client):
        await client.post(
            "/sessions/",
            json={
                "track_name": "Monza",
                "car_name": "Car A",
                "session_type": "practice",
            },
        )
        await client.post(
            "/sessions/",
            json={
                "track_name": "Monza",
                "car_name": "Car A",
                "session_type": "race",
            },
        )

        resp = await client.get("/sessions/?session_type=race")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["session_type"] == "race"


class TestGetSession:
    async def test_get_existing_session(self, client, sample_session_data):
        create_resp = await client.post("/sessions/", json=sample_session_data)
        session_id = create_resp.json()["id"]

        resp = await client.get(f"/sessions/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == session_id
        assert data["frame_count"] == 0
        assert data["duration_seconds"] is None

    async def test_get_nonexistent_session_returns_404(self, client):
        resp = await client.get("/sessions/99999")
        assert resp.status_code == 404


class TestUpdateSession:
    async def test_end_session(self, client, sample_session_data):
        create_resp = await client.post("/sessions/", json=sample_session_data)
        session_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/sessions/{session_id}",
            json={"ended_at": "2026-03-24T16:00:00Z"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ended_at"] is not None

    async def test_update_nonexistent_returns_404(self, client):
        resp = await client.patch(
            "/sessions/99999",
            json={"total_laps": 10},
        )
        assert resp.status_code == 404
