"""Integration tests for emotion API routes."""
import io
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from api.models.emotion_schemas import SessionResponse
from api.routes.emotion import _analyzer, get_repo, router
from services.emotion_analyzer import AnalysisResult, FaceAnalysis
from services.emotion_repository import EmotionRepository


@pytest.fixture
def mock_repo():
    return AsyncMock(spec=EmotionRepository)


@pytest.fixture
def test_app(mock_repo):
    """FastAPI app with emotion routes and mocked dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/emotion")
    app.dependency_overrides[get_repo] = lambda: mock_repo
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


def _make_session(
    title="Test Lesson",
    ended_at=None,
):
    session = MagicMock()
    session.id = uuid.uuid4()
    session.title = title
    session.user_id = None
    session.started_at = datetime.now(timezone.utc)
    session.ended_at = ended_at
    session.created_at = datetime.now(timezone.utc)
    return session


def _make_snapshot(session_id, faces_data=None):
    snapshot = MagicMock()
    snapshot.id = uuid.uuid4()
    snapshot.session_id = session_id
    snapshot.captured_at = datetime.now(timezone.utc)
    snapshot.face_count = len(faces_data) if faces_data else 0
    snapshot.processing_ms = 150.0

    face_results = []
    for fd in (faces_data or []):
        fr = MagicMock()
        fr.face_index = fd["face_index"]
        fr.bbox_x = 10
        fr.bbox_y = 20
        fr.bbox_w = 100
        fr.bbox_h = 100
        fr.dominant_emotion = fd["dominant_emotion"]
        fr.emotion_scores = fd["emotion_scores"]
        fr.engagement_level = fd["engagement_level"]
        fr.engagement_score = fd["engagement_score"]
        face_results.append(fr)
    snapshot.face_results = face_results
    return snapshot


def _jpeg_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (48, 48), (128, 128, 128)).save(buf, format="JPEG")
    return buf.getvalue()


class TestCreateSession:
    def test_creates_session(self, client, mock_repo):
        session = _make_session()
        mock_repo.create_session.return_value = session

        resp = client.post("/emotion/sessions", json={"title": "Math Lesson"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == session.title
        mock_repo.create_session.assert_awaited_once()


class TestListSessions:
    def test_lists_empty(self, client, mock_repo):
        mock_repo.list_sessions.return_value = []
        resp = client.get("/emotion/sessions")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetSession:
    def test_returns_404_when_missing(self, client, mock_repo):
        mock_repo.get_session.return_value = None
        resp = client.get(f"/emotion/sessions/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestEndSession:
    def test_ends_session(self, client, mock_repo):
        session = _make_session(ended_at=datetime.now(timezone.utc))
        mock_repo.end_session.return_value = session

        resp = client.patch(f"/emotion/sessions/{uuid.uuid4()}/end")
        assert resp.status_code == 200
        assert resp.json()["ended_at"] is not None

    def test_returns_404_when_missing(self, client, mock_repo):
        mock_repo.end_session.return_value = None
        resp = client.patch(f"/emotion/sessions/{uuid.uuid4()}/end")
        assert resp.status_code == 404


class TestUploadSnapshot:
    @patch.object(_analyzer, "analyze_image")
    def test_analyzes_image(self, mock_analyze, client, mock_repo):
        session = _make_session()
        mock_repo.get_session.return_value = session

        face = FaceAnalysis(
            face_index=0,
            bbox_x=10, bbox_y=20, bbox_w=100, bbox_h=100,
            dominant_emotion="happy",
            emotion_scores={"happy": 80.0, "neutral": 20.0},
            engagement_level="engaged",
            engagement_score=0.8,
        )
        mock_analyze.return_value = AnalysisResult(faces=[face], processing_ms=123.4)

        snapshot = _make_snapshot(
            session.id,
            [
                {
                    "face_index": 0,
                    "dominant_emotion": "happy",
                    "emotion_scores": {"happy": 80.0, "neutral": 20.0},
                    "engagement_level": "engaged",
                    "engagement_score": 0.8,
                }
            ],
        )
        mock_repo.save_snapshot.return_value = snapshot

        resp = client.post(
            f"/emotion/sessions/{session.id}/snapshots",
            files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["face_count"] == 1
        assert data["faces"][0]["dominant_emotion"] == "happy"

    def test_rejects_ended_session(self, client, mock_repo):
        session = _make_session(ended_at=datetime.now(timezone.utc))
        mock_repo.get_session.return_value = session

        resp = client.post(
            f"/emotion/sessions/{session.id}/snapshots",
            files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 400

    def test_rejects_missing_session(self, client, mock_repo):
        mock_repo.get_session.return_value = None
        resp = client.post(
            f"/emotion/sessions/{uuid.uuid4()}/snapshots",
            files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 404


class TestSessionSummary:
    def test_returns_summary(self, client, mock_repo):
        sid = uuid.uuid4()
        mock_repo.get_session_summary.return_value = {
            "session_id": sid,
            "title": "Test",
            "duration_seconds": 120.0,
            "total_snapshots": 10,
            "total_faces_detected": 25,
            "avg_engagement_score": 0.65,
            "engagement_distribution": {"engaged": 15, "passive": 8, "confused": 2},
            "emotion_distribution": {"happy": 15, "neutral": 10},
        }
        resp = client.get(f"/emotion/sessions/{sid}/summary")
        assert resp.status_code == 200
        assert resp.json()["avg_engagement_score"] == 0.65

    def test_returns_404_when_missing(self, client, mock_repo):
        mock_repo.get_session_summary.return_value = None
        resp = client.get(f"/emotion/sessions/{uuid.uuid4()}/summary")
        assert resp.status_code == 404


class TestTimeline:
    def test_returns_empty_timeline(self, client, mock_repo):
        mock_repo.get_timeline.return_value = []
        resp = client.get(f"/emotion/sessions/{uuid.uuid4()}/timeline")
        assert resp.status_code == 200
        assert resp.json() == []
