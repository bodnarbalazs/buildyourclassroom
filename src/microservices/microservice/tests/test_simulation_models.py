"""Tests for simulation Pydantic models."""
import pytest
from pydantic import ValidationError

from api.models.simulation import (
    ScheduleEvent,
    SimulateRequest,
    SimulateResponse,
    StudentSnapshot,
    TickSnapshot,
)


class TestScheduleEvent:
    def test_valid(self):
        e = ScheduleEvent(time=5, action=1)
        assert e.time == 5
        assert e.action == 1
        assert e.duration == 0

    def test_with_duration(self):
        e = ScheduleEvent(time=10, action=3, duration=5)
        assert e.duration == 5

    def test_time_must_be_positive(self):
        with pytest.raises(ValidationError):
            ScheduleEvent(time=0, action=1)

    def test_action_range(self):
        with pytest.raises(ValidationError):
            ScheduleEvent(time=1, action=0)
        with pytest.raises(ValidationError):
            ScheduleEvent(time=1, action=7)


class TestSimulateRequest:
    def test_defaults(self):
        req = SimulateRequest(ca_schedule=[])
        assert req.rows == 5
        assert req.cols == 6
        assert req.cycles == 45
        assert req.max_engagement == 5
        assert req.seed is None

    def test_custom_values(self):
        req = SimulateRequest(
            ca_schedule=[ScheduleEvent(time=1, action=5)],
            rows=4,
            cols=8,
            cycles=30,
            seed=42,
        )
        assert req.rows == 4
        assert req.cols == 8
        assert req.cycles == 30
        assert len(req.ca_schedule) == 1

    def test_rows_must_be_positive(self):
        with pytest.raises(ValidationError):
            SimulateRequest(ca_schedule=[], rows=0)

    def test_cycles_max(self):
        with pytest.raises(ValidationError):
            SimulateRequest(ca_schedule=[], cycles=121)


class TestStudentSnapshot:
    def test_valid(self):
        s = StudentSnapshot(id=0, engagement=3, emotion="passive")
        assert s.id == 0
        assert s.emotion == "passive"

    def test_invalid_emotion(self):
        with pytest.raises(ValidationError):
            StudentSnapshot(id=0, engagement=3, emotion="happy")


class TestTickSnapshot:
    def test_valid(self):
        tick = TickSnapshot(
            cycle=0,
            students=[StudentSnapshot(id=0, engagement=5, emotion="engaged")],
            avg_engagement=5.0,
        )
        assert tick.cycle == 0
        assert len(tick.students) == 1


class TestSimulateResponse:
    def test_valid(self):
        resp = SimulateResponse(
            rows=5,
            cols=6,
            cycles=10,
            max_engagement=5,
            ticks=[
                TickSnapshot(
                    cycle=0,
                    students=[StudentSnapshot(id=0, engagement=3, emotion="passive")],
                    avg_engagement=3.0,
                )
            ],
        )
        assert resp.rows == 5
        assert len(resp.ticks) == 1
