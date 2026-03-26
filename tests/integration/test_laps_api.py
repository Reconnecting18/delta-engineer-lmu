"""Integration tests for lap analysis API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.fixture
async def session_with_laps(client: AsyncClient) -> dict:
    """Create a session and ingest telemetry frames spanning 3 laps."""
    # Create session
    resp = await client.post(
        "/sessions/",
        json={
            "track_name": "Le Mans 24h Circuit",
            "car_name": "Toyota GR010 Hybrid",
            "driver_name": "Test Driver",
            "session_type": "practice",
        },
    )
    session = resp.json()
    session_id = session["id"]

    # Build frames: 3 laps, each with 3 sectors
    frames = []
    base_offset = 0
    for lap in range(1, 4):
        for sector in range(1, 4):
            for i in range(5):
                offset = base_offset + i * 5
                frames.append(
                    {
                        "timestamp": (
                            f"2026-03-24T14:{offset // 60:02d}" f":{offset % 60:02d}Z"
                        ),
                        "lap_number": lap,
                        "sector": sector,
                        "throttle": 0.8,
                        "brake": 0.0,
                        "steering": 0.0,
                        "gear": 4,
                        "speed": 200.0 + (sector * 10) + i,
                        "rpm": 8000.0,
                        "fuel_level": 50.0 - (lap * 2) - (sector * 0.3) - (i * 0.05),
                        "tire_temps": {
                            "front_left": 90.0 + lap,
                            "front_right": 91.0 + lap,
                            "rear_left": 93.0 + lap,
                            "rear_right": 92.0 + lap,
                        },
                    }
                )
            base_offset += 25

    # Ingest frames
    await client.post(
        "/telemetry/",
        json={"session_id": session_id, "frames": frames},
    )

    return {"session_id": session_id, "session": session}


# ---------------------------------------------------------------------------
# POST /sessions/{id}/laps/compute
# ---------------------------------------------------------------------------


class TestComputeSessionLaps:
    @pytest.mark.asyncio
    async def test_compute_laps_returns_summaries(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        resp = await client.post(f"/sessions/{sid}/laps/compute")
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 3  # 3 laps
        assert data[0]["lap_number"] == 1
        assert data[1]["lap_number"] == 2
        assert data[2]["lap_number"] == 3

    @pytest.mark.asyncio
    async def test_compute_laps_has_sector_times(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        resp = await client.post(f"/sessions/{sid}/laps/compute")
        data = resp.json()
        lap = data[0]
        assert lap["sector_1_time"] is not None
        assert lap["sector_2_time"] is not None
        assert lap["sector_3_time"] is not None

    @pytest.mark.asyncio
    async def test_compute_laps_has_speed_stats(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        resp = await client.post(f"/sessions/{sid}/laps/compute")
        data = resp.json()
        lap = data[0]
        assert lap["top_speed"] > 0
        assert lap["average_speed"] > 0

    @pytest.mark.asyncio
    async def test_compute_laps_has_fuel_data(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        resp = await client.post(f"/sessions/{sid}/laps/compute")
        data = resp.json()
        lap = data[0]
        assert lap["fuel_used"] >= 0
        assert lap["fuel_level_start"] > 0

    @pytest.mark.asyncio
    async def test_compute_laps_404_missing_session(self, client: AsyncClient):
        resp = await client.post("/sessions/9999/laps/compute")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_compute_laps_idempotent(
        self, client: AsyncClient, session_with_laps: dict
    ):
        """Computing laps twice produces the same results."""
        sid = session_with_laps["session_id"]
        resp1 = await client.post(f"/sessions/{sid}/laps/compute")
        resp2 = await client.post(f"/sessions/{sid}/laps/compute")
        assert resp1.json() == resp2.json()

    @pytest.mark.asyncio
    async def test_compute_updates_best_lap_time(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        await client.post(f"/sessions/{sid}/laps/compute")
        resp = await client.get(f"/sessions/{sid}")
        session = resp.json()
        assert session["best_lap_time"] is not None
        assert session["best_lap_time"] > 0


# ---------------------------------------------------------------------------
# GET /sessions/{id}/laps
# ---------------------------------------------------------------------------


class TestListSessionLaps:
    @pytest.mark.asyncio
    async def test_list_laps_empty_before_compute(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        resp = await client.get(f"/sessions/{sid}/laps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_list_laps_after_compute(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        await client.post(f"/sessions/{sid}/laps/compute")
        resp = await client.get(f"/sessions/{sid}/laps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_laps_sorted_by_lap_time(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        await client.post(f"/sessions/{sid}/laps/compute")
        resp = await client.get(f"/sessions/{sid}/laps?sort_by=lap_time")
        data = resp.json()
        times = [item["lap_time"] for item in data["items"]]
        assert times == sorted(times)

    @pytest.mark.asyncio
    async def test_list_laps_pagination(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        await client.post(f"/sessions/{sid}/laps/compute")
        resp = await client.get(f"/sessions/{sid}/laps?page=1&limit=2")
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["pages"] == 2

    @pytest.mark.asyncio
    async def test_list_laps_404_missing_session(self, client: AsyncClient):
        resp = await client.get("/sessions/9999/laps")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /laps/compare
# ---------------------------------------------------------------------------


class TestCompareLaps:
    @pytest.mark.asyncio
    async def test_compare_two_laps(self, client: AsyncClient, session_with_laps: dict):
        sid = session_with_laps["session_id"]
        compute_resp = await client.post(f"/sessions/{sid}/laps/compute")
        laps = compute_resp.json()
        id_a = laps[0]["id"]
        id_b = laps[1]["id"]

        resp = await client.get(f"/laps/compare?ids={id_a},{id_b}")
        assert resp.status_code == 200
        data = resp.json()
        assert "lap_a" in data
        assert "lap_b" in data
        assert "time_delta" in data
        assert "sector_deltas" in data
        assert "speed_trace" in data
        assert "input_trace" in data
        assert len(data["sector_deltas"]) == 3

    @pytest.mark.asyncio
    async def test_compare_has_speed_trace(
        self, client: AsyncClient, session_with_laps: dict
    ):
        sid = session_with_laps["session_id"]
        compute_resp = await client.post(f"/sessions/{sid}/laps/compute")
        laps = compute_resp.json()

        resp = await client.get(
            f"/laps/compare?ids={laps[0]['id']},{laps[1]['id']}&sample_points=20"
        )
        data = resp.json()
        assert len(data["speed_trace"]) == 21  # 0 through 20 inclusive
        assert len(data["input_trace"]) == 21

    @pytest.mark.asyncio
    async def test_compare_wrong_number_of_ids(self, client: AsyncClient):
        resp = await client.get("/laps/compare?ids=1")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_compare_invalid_ids(self, client: AsyncClient):
        resp = await client.get("/laps/compare?ids=abc,def")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_compare_404_missing_lap(self, client: AsyncClient):
        resp = await client.get("/laps/compare?ids=9999,9998")
        assert resp.status_code == 404
