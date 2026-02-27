"""Integration tests for agenda API routes."""
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openai import OpenAIError

from api.models.agenda import LessonAgenda
from api.routes.agenda import router
from services.agenda_generator import AgendaGenerationError


def _valid_agenda_data():
    return {
        "lesson_title": "Intro to Fractions",
        "subject": "Math",
        "target_audience": "Grade 5",
        "total_duration_minutes": 20,
        "overall_objectives": ["Understand fractions"],
        "sections": [
            {
                "order": 1,
                "title": "Lecture",
                "description": "Teach fractions",
                "start_minute": 1,
                "duration_minutes": 10,
                "learning_objectives": ["Identify fractions"],
                "element": {
                    "element_type": "LECTURE",
                    "pedagogical_rationale": "Foundation building",
                    "key_points": ["numerator", "denominator"],
                    "instructor_notes": "Use visual aids",
                },
            },
            {
                "order": 2,
                "title": "Game",
                "description": "Practice",
                "start_minute": 11,
                "duration_minutes": 10,
                "learning_objectives": ["Apply fractions"],
                "element": {
                    "element_type": "GAME_CHALLENGE",
                    "pedagogical_rationale": "Engagement boost",
                    "game_title": "Fraction Race",
                    "rules": "First to solve wins",
                    "team_based": True,
                },
            },
        ],
        "summary": "Covered fractions basics",
    }


@pytest.fixture
def mock_generator():
    agenda = LessonAgenda.model_validate(_valid_agenda_data())
    gen = AsyncMock()
    gen.generate.return_value = agenda
    return gen


@pytest.fixture
def test_app(mock_generator):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    with patch("api.routes.agenda._get_generator", return_value=mock_generator):
        yield app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


_REQUEST_BODY = {
    "subject": "Math",
    "topic": "Fractions",
    "target_audience": "Grade 5",
    "duration_minutes": 20,
}


class TestGenerateAgendaHappyPath:
    def test_returns_200(self, client):
        resp = client.post("/api/v1/generate-agenda", json=_REQUEST_BODY)
        assert resp.status_code == 200

    def test_response_has_ca_schedule(self, client):
        resp = client.post("/api/v1/generate-agenda", json=_REQUEST_BODY)
        data = resp.json()
        assert "ca_schedule" in data
        assert isinstance(data["ca_schedule"], list)
        assert len(data["ca_schedule"]) == 2

    def test_response_has_all_agenda_fields(self, client):
        resp = client.post("/api/v1/generate-agenda", json=_REQUEST_BODY)
        data = resp.json()
        assert data["lesson_title"] == "Intro to Fractions"
        assert data["subject"] == "Math"
        assert len(data["sections"]) == 2

    def test_ca_schedule_game_has_duration(self, client):
        resp = client.post("/api/v1/generate-agenda", json=_REQUEST_BODY)
        schedule = resp.json()["ca_schedule"]
        game_entry = next(e for e in schedule if e["action"] == 6)
        assert "duration" in game_entry


class TestGenerateAgendaErrors:
    def test_agenda_generation_error_returns_502(self, client, mock_generator):
        mock_generator.generate.side_effect = AgendaGenerationError("parse failed")
        resp = client.post("/api/v1/generate-agenda", json=_REQUEST_BODY)
        assert resp.status_code == 502
        assert "parse failed" in resp.json()["detail"]

    def test_openai_error_returns_502(self, client, mock_generator):
        mock_generator.generate.side_effect = OpenAIError("rate limit")
        resp = client.post("/api/v1/generate-agenda", json=_REQUEST_BODY)
        assert resp.status_code == 502
        assert "Azure OpenAI service error" in resp.json()["detail"]

    def test_unexpected_error_is_not_caught(self, client, mock_generator):
        mock_generator.generate.side_effect = RuntimeError("unexpected")
        with pytest.raises(RuntimeError, match="unexpected"):
            client.post("/api/v1/generate-agenda", json=_REQUEST_BODY)

    def test_invalid_request_body_returns_422(self, client):
        resp = client.post("/api/v1/generate-agenda", json={"subject": "Math"})
        assert resp.status_code == 422
