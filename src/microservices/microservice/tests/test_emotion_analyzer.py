"""Tests for services/emotion_analyzer.py."""
import io
from unittest.mock import patch

import numpy as np
from PIL import Image

from services.emotion_analyzer import (
    AnalysisResult,
    EmotionAnalyzer,
    FaceAnalysis,
    _crop_face,
    compute_engagement,
)


def _make_image_bytes(w=200, h=200):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (128, 128, 128)).save(buf, format="JPEG")
    return buf.getvalue()


def _fake_emotion_result(dominant="happy"):
    return {
        "emotion": {
            "happy": 70.0, "sad": 5.0, "angry": 3.0, "surprise": 10.0,
            "fear": 2.0, "disgust": 2.0, "neutral": 8.0,
        },
        "dominant_emotion": dominant,
    }


def _fake_detected_face(x, y, w, h):
    return {"facial_area": {"x": x, "y": y, "w": w, "h": h}, "confidence": 0.99}


class TestComputeEngagement:
    def test_happy_face_is_engaged(self):
        scores = {
            "happy": 90.0, "sad": 2.0, "angry": 1.0, "surprise": 3.0,
            "fear": 1.0, "disgust": 1.0, "neutral": 2.0,
        }
        level, score = compute_engagement(scores)
        assert level == "engaged"
        assert score > 0.5

    def test_neutral_face_is_passive(self):
        scores = {
            "happy": 5.0, "sad": 5.0, "angry": 2.0, "surprise": 3.0,
            "fear": 2.0, "disgust": 3.0, "neutral": 80.0,
        }
        level, score = compute_engagement(scores)
        assert level == "passive"

    def test_sad_face_is_anxious(self):
        scores = {
            "happy": 2.0, "sad": 60.0, "angry": 5.0, "surprise": 1.0,
            "fear": 25.0, "disgust": 2.0, "neutral": 5.0,
        }
        level, score = compute_engagement(scores)
        assert level == "anxious"

    def test_angry_face_is_disruptive(self):
        scores = {
            "happy": 2.0, "sad": 3.0, "angry": 70.0, "surprise": 2.0,
            "fear": 3.0, "disgust": 15.0, "neutral": 5.0,
        }
        level, score = compute_engagement(scores)
        assert level == "disruptive"

    def test_mixed_signals_is_confused(self):
        scores = {
            "happy": 20.0, "sad": 15.0, "angry": 10.0, "surprise": 15.0,
            "fear": 10.0, "disgust": 10.0, "neutral": 20.0,
        }
        level, score = compute_engagement(scores)
        assert level == "confused"

    def test_score_clamped_to_0_1(self):
        scores = {"happy": 0.0, "sad": 0.0, "angry": 0.0, "neutral": 0.0}
        _, score = compute_engagement(scores)
        assert 0.0 <= score <= 1.0

    def test_empty_scores_is_confused(self):
        level, score = compute_engagement({})
        assert level == "confused"
        assert score == 0.3


class TestCropFace:
    def test_clips_to_image_bounds(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        crop = _crop_face(frame, {"x": 90, "y": 90, "w": 30, "h": 30}, padding_pct=0.2)
        assert crop.shape[0] <= 100 and crop.shape[0] > 0
        assert crop.shape[1] <= 100 and crop.shape[1] > 0

    def test_clips_negative_origin(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        crop = _crop_face(frame, {"x": 0, "y": 0, "w": 20, "h": 20}, padding_pct=0.5)
        assert crop.shape[0] > 0 and crop.shape[1] > 0

    def test_applies_padding(self):
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        region = {"x": 50, "y": 50, "w": 40, "h": 40}
        no_pad = _crop_face(frame, region, padding_pct=0.0)
        with_pad = _crop_face(frame, region, padding_pct=0.25)
        assert with_pad.shape[0] > no_pad.shape[0]
        assert with_pad.shape[1] > no_pad.shape[1]

    def test_zero_padding_exact_crop(self):
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        crop = _crop_face(frame, {"x": 50, "y": 60, "w": 40, "h": 30}, padding_pct=0.0)
        assert crop.shape == (30, 40, 3)


class TestAnalyzeSingleFace:
    @patch("services.emotion_analyzer.DeepFace.analyze")
    def test_returns_face_analysis(self, mock_analyze):
        mock_analyze.return_value = [_fake_emotion_result()]
        analyzer = EmotionAnalyzer()
        bbox = {"x": 10, "y": 20, "w": 100, "h": 100}

        result = analyzer._analyze_single_face(np.zeros((48, 48, 3), dtype=np.uint8), 0, bbox)

        assert isinstance(result, FaceAnalysis)
        assert result.face_index == 0
        assert result.bbox_x == 10 and result.bbox_y == 20
        assert result.bbox_w == 100 and result.bbox_h == 100
        assert result.dominant_emotion == "happy"
        assert result.engagement_level == "engaged"
        assert mock_analyze.call_args.kwargs["detector_backend"] == "skip"


class TestTwoStagePipeline:
    @patch("services.emotion_analyzer.DeepFace.analyze")
    @patch("services.emotion_analyzer.DeepFace.extract_faces")
    def test_single_face(self, mock_extract, mock_analyze):
        mock_extract.return_value = [_fake_detected_face(10, 20, 50, 50)]
        mock_analyze.return_value = [_fake_emotion_result()]

        result = EmotionAnalyzer().analyze_image(_make_image_bytes())

        assert isinstance(result, AnalysisResult)
        assert len(result.faces) == 1
        assert result.faces[0].bbox_x == 10
        assert result.faces[0].dominant_emotion == "happy"
        assert result.processing_ms >= 0

    @patch("services.emotion_analyzer.DeepFace.analyze")
    @patch("services.emotion_analyzer.DeepFace.extract_faces")
    def test_multi_face_preserves_ordering(self, mock_extract, mock_analyze):
        mock_extract.return_value = [
            _fake_detected_face(10, 10, 30, 30),
            _fake_detected_face(80, 80, 30, 30),
            _fake_detected_face(50, 50, 30, 30),
        ]
        mock_analyze.return_value = [_fake_emotion_result()]

        result = EmotionAnalyzer().analyze_image(_make_image_bytes())

        assert len(result.faces) == 3
        assert [f.face_index for f in result.faces] == [0, 1, 2]

    @patch("services.emotion_analyzer.DeepFace.extract_faces")
    def test_empty_image_no_faces(self, mock_extract):
        mock_extract.return_value = []

        result = EmotionAnalyzer().analyze_image(_make_image_bytes())

        assert result.faces == []
        assert result.processing_ms >= 0

    @patch("services.emotion_analyzer.DeepFace.extract_faces")
    def test_fallback_when_extract_fails(self, mock_extract):
        mock_extract.side_effect = RuntimeError("detector crashed")

        result = EmotionAnalyzer().analyze_image(_make_image_bytes())

        assert result.faces == []
        assert result.processing_ms >= 0

    @patch("services.emotion_analyzer.DeepFace.analyze")
    @patch("services.emotion_analyzer.DeepFace.extract_faces")
    def test_skips_zero_size_faces(self, mock_extract, mock_analyze):
        mock_extract.return_value = [
            _fake_detected_face(10, 10, 0, 0),
            _fake_detected_face(50, 50, 30, 30),
        ]
        mock_analyze.return_value = [_fake_emotion_result()]

        result = EmotionAnalyzer().analyze_image(_make_image_bytes())

        assert len(result.faces) == 1

    @patch("services.emotion_analyzer.DeepFace.analyze")
    @patch("services.emotion_analyzer.DeepFace.extract_faces")
    def test_single_face_analyze_failure_skipped(self, mock_extract, mock_analyze):
        mock_extract.return_value = [
            _fake_detected_face(10, 10, 30, 30),
            _fake_detected_face(80, 80, 30, 30),
        ]
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("model crash")
            return [_fake_emotion_result()]

        mock_analyze.side_effect = side_effect

        result = EmotionAnalyzer().analyze_image(_make_image_bytes())

        assert len(result.faces) == 1
