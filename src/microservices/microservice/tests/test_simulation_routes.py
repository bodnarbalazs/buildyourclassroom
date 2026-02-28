"""Integration tests for simulation API routes."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.simulation import router


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


_SCHEDULE = [
    {"time": 5, "action": 1},
    {"time": 10, "action": 2},
    {"time": 15, "action": 3, "duration": 5},
    {"time": 25, "action": 4},
    {"time": 35, "action": 5},
]


class TestSimulateHappyPath:
    def test_returns_200(self, client):
        resp = client.post("/api/v1/simulate", json={"ca_schedule": _SCHEDULE, "seed": 42})
        assert resp.status_code == 200

    def test_response_has_ticks(self, client):
        resp = client.post("/api/v1/simulate", json={"ca_schedule": [], "seed": 42})
        data = resp.json()
        # Default 45 cycles = 46 ticks (initial + 45)
        assert len(data["ticks"]) == 46

    def test_tick_has_correct_student_count(self, client):
        resp = client.post("/api/v1/simulate", json={"ca_schedule": [], "seed": 42})
        data = resp.json()
        # Default 5x6 = 30 students
        for tick in data["ticks"]:
            assert len(tick["students"]) == 30

    def test_custom_grid_size(self, client):
        resp = client.post("/api/v1/simulate", json={
            "ca_schedule": [],
            "rows": 3,
            "cols": 4,
            "cycles": 5,
            "seed": 42,
        })
        data = resp.json()
        assert data["rows"] == 3
        assert data["cols"] == 4
        assert len(data["ticks"]) == 6
        assert len(data["ticks"][0]["students"]) == 12

    def test_students_have_emotion_field(self, client):
        resp = client.post("/api/v1/simulate", json={"ca_schedule": [], "cycles": 3, "seed": 42})
        data = resp.json()
        valid_emotions = {"engaged", "passive", "anxious", "confused", "disruptive"}
        for tick in data["ticks"]:
            for student in tick["students"]:
                assert student["emotion"] in valid_emotions

    def test_deterministic_with_seed(self, client):
        body = {"ca_schedule": _SCHEDULE, "seed": 42}
        a = client.post("/api/v1/simulate", json=body).json()
        b = client.post("/api/v1/simulate", json=body).json()
        assert a == b

    def test_schedule_affects_outcome(self, client):
        no_schedule = client.post("/api/v1/simulate", json={
            "ca_schedule": [], "seed": 42, "cycles": 10,
        }).json()
        with_schedule = client.post("/api/v1/simulate", json={
            "ca_schedule": [{"time": 1, "action": 5}], "seed": 42, "cycles": 10,
        }).json()
        # Energizer at t=1 should make the results different
        assert no_schedule["ticks"][-1] != with_schedule["ticks"][-1]


class TestSimulateValidation:
    def test_invalid_action_returns_422(self, client):
        resp = client.post("/api/v1/simulate", json={
            "ca_schedule": [{"time": 1, "action": 99}],
        })
        assert resp.status_code == 422

    def test_missing_schedule_returns_422(self, client):
        resp = client.post("/api/v1/simulate", json={})
        assert resp.status_code == 422

    def test_negative_cycles_returns_422(self, client):
        resp = client.post("/api/v1/simulate", json={
            "ca_schedule": [], "cycles": 0,
        })
        assert resp.status_code == 422
