"""Integration tests for assessment API routes."""
import json
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openai import OpenAIError

from api.models.assessment import AssessmentBundle
from api.routes.assessment import router
from services.assessment_generator import AssessmentGenerationError
from services.transcription_service import TranscriptionError, TranscriptionResult


def _mc_q(text="What is 2+2?"):
    return {
        "question_type": "multiple_choice",
        "question_text": text,
        "options": ["1", "2", "3", "4"],
        "correct_answer": "4",
        "explanation": "Arithmetic",
        "difficulty": "easy",
    }


def _tf_q(text="True or false."):
    return {
        "question_type": "true_false",
        "question_text": text,
        "correct_answer": True,
        "explanation": "Fact",
        "difficulty": "easy",
    }


_NOW = datetime.now(tz=timezone.utc).isoformat()


def _valid_bundle_data():
    quiz_questions = [_mc_q(f"Q{i}?") for i in range(3)] + [
        _tf_q(f"TF{i}?") for i in range(2)
    ]
    return {
        "transcript_summary": "A lesson summary.",
        "quiz": {
            "title": "Quiz",
            "subject": "Science",
            "generated_from": "test.mp3",
            "assessment_type": "quiz",
            "total_questions": 5,
            "created_at": _NOW,
            "questions": quiz_questions,
        },
        "practice_test": {
            "title": "Practice",
            "subject": "Science",
            "generated_from": "test.mp3",
            "assessment_type": "practice_test",
            "total_questions": 1,
            "created_at": _NOW,
            "sections": [
                {
                    "section_title": "Basics",
                    "questions": [
                        {
                            "base": _mc_q(),
                            "topic_tag": "basics",
                            "bloom_level": "remember",
                        }
                    ],
                }
            ],
        },
        "exam": {
            "title": "Exam",
            "subject": "Science",
            "generated_from": "test.mp3",
            "assessment_type": "exam",
            "total_questions": 1,
            "created_at": _NOW,
            "total_points": 10,
            "time_limit_minutes": 60,
            "sections": [
                {
                    "section_title": "Exam Section",
                    "questions": [
                        {
                            "base": _tf_q(),
                            "topic_tag": "basics",
                            "bloom_level": "understand",
                            "points": 10,
                        }
                    ],
                }
            ],
        },
    }


@pytest.fixture
def mock_bundle():
    return AssessmentBundle.model_validate(_valid_bundle_data())


@pytest.fixture
def mock_transcription():
    return TranscriptionResult(text="This is a lesson about science.", segments=[])


@pytest.fixture
def mock_generator(mock_bundle):
    gen = AsyncMock()
    gen.generate.return_value = mock_bundle
    return gen


@pytest.fixture
def mock_transcriber(mock_transcription):
    svc = AsyncMock()
    svc.transcribe_file.return_value = mock_transcription
    return svc


@pytest.fixture
def test_app(mock_generator, mock_transcriber):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    with (
        patch("api.routes.assessment._get_assessment_generator", return_value=mock_generator),
        patch(
            "api.routes.assessment._get_transcription_service", return_value=mock_transcriber
        ),
    ):
        yield app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestFromTranscriptEndpoint:
    def test_returns_200(self, client):
        resp = client.post(
            "/api/v1/generate-assessments/from-transcript",
            json={"transcript": "This is a lesson."},
        )
        assert resp.status_code == 200

    def test_returns_bundle(self, client):
        resp = client.post(
            "/api/v1/generate-assessments/from-transcript",
            json={"transcript": "This is a lesson."},
        )
        data = resp.json()
        assert "transcript_summary" in data
        assert "quiz" in data
        assert "practice_test" in data
        assert "exam" in data

    def test_empty_transcript_returns_400(self, client):
        resp = client.post(
            "/api/v1/generate-assessments/from-transcript",
            json={"transcript": "   "},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_missing_transcript_returns_422(self, client):
        resp = client.post(
            "/api/v1/generate-assessments/from-transcript",
            json={},
        )
        assert resp.status_code == 422

    def test_with_optional_fields(self, client, mock_generator):
        resp = client.post(
            "/api/v1/generate-assessments/from-transcript",
            json={
                "transcript": "A lesson.",
                "subject": "Physics",
                "target_audience": "Grade 10",
                "additional_instructions": "Be thorough",
            },
        )
        assert resp.status_code == 200
        call_kwargs = mock_generator.generate.call_args.kwargs
        assert call_kwargs["subject"] == "Physics"
        assert call_kwargs["target_audience"] == "Grade 10"
        assert call_kwargs["additional_instructions"] == "Be thorough"


class TestFromTranscriptErrors:
    def test_generation_error_returns_502(self, client, mock_generator):
        mock_generator.generate.side_effect = AssessmentGenerationError("parse failed")
        resp = client.post(
            "/api/v1/generate-assessments/from-transcript",
            json={"transcript": "A lesson."},
        )
        assert resp.status_code == 502
        assert "parse failed" in resp.json()["detail"]

    def test_openai_error_returns_502(self, client, mock_generator):
        mock_generator.generate.side_effect = OpenAIError("rate limit")
        resp = client.post(
            "/api/v1/generate-assessments/from-transcript",
            json={"transcript": "A lesson."},
        )
        assert resp.status_code == 502
        assert "Azure OpenAI service error" in resp.json()["detail"]


class TestFileUploadEndpoint:
    def test_returns_200_with_txt(self, client):
        resp = client.post(
            "/api/v1/generate-assessments",
            files={"file": ("lesson.txt", b"A lesson transcript.", "text/plain")},
        )
        assert resp.status_code == 200

    def test_returns_200_with_mp3(self, client):
        resp = client.post(
            "/api/v1/generate-assessments",
            files={"file": ("recording.mp3", b"fake audio bytes", "audio/mpeg")},
        )
        assert resp.status_code == 200

    def test_unsupported_format_returns_400(self, client):
        resp = client.post(
            "/api/v1/generate-assessments",
            files={"file": ("doc.pdf", b"pdf content", "application/pdf")},
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    def test_empty_file_returns_400(self, client):
        resp = client.post(
            "/api/v1/generate-assessments",
            files={"file": ("empty.mp3", b"", "audio/mpeg")},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_includes_optional_form_fields(self, client, mock_generator):
        resp = client.post(
            "/api/v1/generate-assessments",
            files={"file": ("lesson.txt", b"content", "text/plain")},
            data={"subject": "Math", "target_audience": "Grade 8"},
        )
        assert resp.status_code == 200
        call_kwargs = mock_generator.generate.call_args.kwargs
        assert call_kwargs["subject"] == "Math"
        assert call_kwargs["target_audience"] == "Grade 8"


class TestFileUploadErrors:
    def test_transcription_error_returns_400(self, client, mock_transcriber):
        mock_transcriber.transcribe_file.side_effect = TranscriptionError("bad audio")
        resp = client.post(
            "/api/v1/generate-assessments",
            files={"file": ("bad.mp3", b"bad", "audio/mpeg")},
        )
        assert resp.status_code == 400
        assert "bad audio" in resp.json()["detail"]

    def test_whisper_openai_error_returns_502(self, client, mock_transcriber):
        mock_transcriber.transcribe_file.side_effect = OpenAIError("timeout")
        resp = client.post(
            "/api/v1/generate-assessments",
            files={"file": ("audio.mp3", b"data", "audio/mpeg")},
        )
        assert resp.status_code == 502
        assert "Whisper" in resp.json()["detail"]

    def test_empty_transcription_returns_400(self, client, mock_transcriber):
        mock_transcriber.transcribe_file.return_value = TranscriptionResult(
            text="   ", segments=[]
        )
        resp = client.post(
            "/api/v1/generate-assessments",
            files={"file": ("audio.mp3", b"data", "audio/mpeg")},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()
