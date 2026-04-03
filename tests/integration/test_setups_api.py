"""Integration tests for car setup endpoints."""

from __future__ import annotations


class TestCreateSetup:
    async def test_create_setup_returns_201(self, client):
        resp = await client.post(
            "/setups/",
            json={
                "name": "Quali low DF",
                "car_name": "Toyota GR010 Hybrid",
                "parameters": {"rear_wing": 7, "front_wing": 5},
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Quali low DF"
        assert data["car_name"] == "Toyota GR010 Hybrid"
        assert data["track_name"] is None
        assert data["session_id"] is None
        assert data["notes"] is None
        assert data["parameters"] == {"rear_wing": 7, "front_wing": 5}
        assert data["source_filename"] is None
        assert data["id"] is not None
        assert data["created_at"] is not None

    async def test_create_setup_with_session(self, client, sample_session_data):
        s = await client.post("/sessions/", json=sample_session_data)
        sid = s.json()["id"]
        resp = await client.post(
            "/setups/",
            json={"name": "Race", "car_name": "Car", "session_id": sid},
        )
        assert resp.status_code == 201
        assert resp.json()["session_id"] == sid

    async def test_create_setup_unknown_session_404(self, client):
        resp = await client.post(
            "/setups/",
            json={"name": "X", "car_name": "Y", "session_id": 99999},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Session not found"


class TestListSetups:
    async def test_list_empty(self, client):
        resp = await client.get("/setups/")
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["pages"] == 0

    async def test_list_pagination_and_filters(self, client):
        await client.post(
            "/setups/",
            json={"name": "A", "car_name": "Car1", "track_name": "Monza"},
        )
        await client.post(
            "/setups/",
            json={"name": "B", "car_name": "Car2", "track_name": "Spa"},
        )

        r_all = await client.get("/setups/")
        assert r_all.json()["total"] == 2

        r_car = await client.get("/setups/?car_name=Car1")
        assert r_car.json()["total"] == 1
        assert r_car.json()["items"][0]["name"] == "A"

        r_track = await client.get("/setups/?track_name=Spa")
        assert r_track.json()["total"] == 1
        assert r_track.json()["items"][0]["name"] == "B"

        r_page = await client.get("/setups/?page=1&limit=1")
        assert r_page.json()["total"] == 2
        assert len(r_page.json()["items"]) == 1
        assert r_page.json()["pages"] == 2

    async def test_filter_by_session_id(self, client, sample_session_data):
        s1 = await client.post("/sessions/", json=sample_session_data)
        s2 = await client.post("/sessions/", json=sample_session_data)
        id1 = s1.json()["id"]
        id2 = s2.json()["id"]
        await client.post(
            "/setups/",
            json={"name": "S1", "car_name": "C", "session_id": id1},
        )
        await client.post(
            "/setups/",
            json={"name": "S2", "car_name": "C", "session_id": id2},
        )
        r = await client.get(f"/setups/?session_id={id1}")
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["name"] == "S1"
