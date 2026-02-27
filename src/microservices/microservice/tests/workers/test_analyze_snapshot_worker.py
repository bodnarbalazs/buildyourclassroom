"""Tests for workers/analyze_snapshot_worker.py callback logic."""

import base64
import io
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from tests.workers.conftest import make_envelope
from workers.analyze_snapshot_worker import make_callback, _build_snapshot_response


def _dummy_image_b64() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (48, 48), (255, 0, 0)).save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()


def _make_snapshot_mock():
    """Build a mock snapshot ORM object with face_results."""
    face = MagicMock()
    face.face_index = 0
    face.bbox_x, face.bbox_y, face.bbox_w, face.bbox_h = 10, 20, 100, 100
    face.dominant_emotion = "happy"
    face.emotion_scores = {"happy": 90.0, "neutral": 10.0}
    face.engagement_level = "engaged"
    face.engagement_score = 0.9

    snapshot = MagicMock()
    snapshot.id = uuid.uuid4()
    snapshot.session_id = uuid.uuid4()
    snapshot.captured_at = datetime.now(timezone.utc)
    snapshot.face_count = 1
    snapshot.processing_ms = 42.0
    snapshot.face_results = [face]
    return snapshot


class TestBuildSnapshotResponse:
    def test_serializes_snapshot(self):
        snapshot = _make_snapshot_mock()
        result = _build_snapshot_response(snapshot)

        assert result["snapshotId"] == str(snapshot.id)
        assert result["sessionId"] == str(snapshot.session_id)
        assert result["faceCount"] == 1
        assert len(result["faces"]) == 1
        assert result["faces"][0]["dominantEmotion"] == "happy"
        assert result["faces"][0]["bbox"] == {"x": 10, "y": 20, "w": 100, "h": 100}


class TestAnalyzeSnapshotCallback:
    @patch("workers.analyze_snapshot_worker._loop")
    @patch("workers.analyze_snapshot_worker._analyzer")
    def test_valid_command_produces_envelope(
        self, mock_analyzer, mock_loop, mock_channel, mock_method, mock_properties
    ):
        snapshot = _make_snapshot_mock()
        session_id = str(snapshot.session_id)

        analysis_result = MagicMock()
        analysis_result.faces = [MagicMock()]
        analysis_result.processing_ms = 42.0
        mock_analyzer.analyze_image.return_value = analysis_result
        mock_loop.run_until_complete.return_value = snapshot

        session_factory = MagicMock()
        callback = make_callback(session_factory)

        body = make_envelope(
            "Hackathon.Domain.Messages:AnalyzeSnapshotCommand",
            {"sessionId": session_id, "imageBase64": _dummy_image_b64()},
        )

        callback(mock_channel, mock_method, mock_properties, body)

        mock_channel.basic_ack.assert_called_once_with(delivery_tag=42)
        mock_channel.basic_publish.assert_called_once()

        published_body = json.loads(mock_channel.basic_publish.call_args.kwargs["body"])
        assert published_body["messageType"] == [
            "urn:message:Hackathon.Domain.Messages:AnalyzeSnapshotResult"
        ]
        assert published_body["correlationId"] == "corr-123"
        assert published_body["message"]["snapshotId"] == str(snapshot.id)

    @patch("workers.analyze_snapshot_worker._loop")
    @patch("workers.analyze_snapshot_worker._analyzer")
    def test_missing_session_id_nacks(
        self, mock_analyzer, mock_loop, mock_channel, mock_method, mock_properties
    ):
        session_factory = MagicMock()
        callback = make_callback(session_factory)

        body = make_envelope(
            "Hackathon.Domain.Messages:AnalyzeSnapshotCommand",
            {"imageBase64": _dummy_image_b64()},
        )

        callback(mock_channel, mock_method, mock_properties, body)

        mock_channel.basic_nack.assert_called_once_with(delivery_tag=42, requeue=False)
        mock_channel.basic_ack.assert_not_called()
        mock_analyzer.analyze_image.assert_not_called()

    @patch("workers.analyze_snapshot_worker._loop")
    @patch("workers.analyze_snapshot_worker._analyzer")
    def test_missing_image_nacks(
        self, mock_analyzer, mock_loop, mock_channel, mock_method, mock_properties
    ):
        session_factory = MagicMock()
        callback = make_callback(session_factory)

        body = make_envelope(
            "Hackathon.Domain.Messages:AnalyzeSnapshotCommand",
            {"sessionId": str(uuid.uuid4())},
        )

        callback(mock_channel, mock_method, mock_properties, body)

        mock_channel.basic_nack.assert_called_once_with(delivery_tag=42, requeue=False)
        mock_channel.basic_ack.assert_not_called()

    @patch("workers.analyze_snapshot_worker._loop")
    @patch("workers.analyze_snapshot_worker._analyzer")
    def test_analyzer_error_nacks(
        self, mock_analyzer, mock_loop, mock_channel, mock_method, mock_properties
    ):
        mock_analyzer.analyze_image.side_effect = RuntimeError("model crash")

        session_factory = MagicMock()
        callback = make_callback(session_factory)

        body = make_envelope(
            "Hackathon.Domain.Messages:AnalyzeSnapshotCommand",
            {"sessionId": str(uuid.uuid4()), "imageBase64": _dummy_image_b64()},
        )

        callback(mock_channel, mock_method, mock_properties, body)

        mock_channel.basic_nack.assert_called_once_with(delivery_tag=42, requeue=False)
        mock_channel.basic_ack.assert_not_called()

    @patch("workers.analyze_snapshot_worker._loop")
    @patch("workers.analyze_snapshot_worker._analyzer")
    def test_reply_uses_response_address_fallback(
        self, mock_analyzer, mock_loop, mock_channel, mock_method, mock_properties
    ):
        """When reply_to is None, the worker falls back to responseAddress."""
        mock_properties.reply_to = None
        mock_properties.correlation_id = "corr-456"

        snapshot = _make_snapshot_mock()
        analysis_result = MagicMock()
        analysis_result.faces = []
        analysis_result.processing_ms = 10.0
        mock_analyzer.analyze_image.return_value = analysis_result
        mock_loop.run_until_complete.return_value = snapshot

        session_factory = MagicMock()
        callback = make_callback(session_factory)

        body = json.dumps({
            "messageType": ["urn:message:Hackathon.Domain.Messages:AnalyzeSnapshotCommand"],
            "message": {
                "sessionId": str(snapshot.session_id),
                "imageBase64": _dummy_image_b64(),
            },
            "responseAddress": "rabbitmq://localhost/fallback-reply-queue?temporary=true",
            "conversationId": "conv-001",
        }).encode()

        callback(mock_channel, mock_method, mock_properties, body)

        mock_channel.basic_publish.assert_called_once()
        assert mock_channel.basic_publish.call_args.kwargs["routing_key"] == "fallback-reply-queue"
