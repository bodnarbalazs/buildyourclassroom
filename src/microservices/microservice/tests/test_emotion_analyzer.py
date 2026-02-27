"""Tests for services/emotion_analyzer.py."""
from unittest.mock import patch

from services.emotion_analyzer import AnalysisResult, compute_engagement, EmotionAnalyzer


class TestComputeEngagement:
    def test_happy_face_is_engaged(self):
        scores = {
            "happy": 90.0,
            "sad": 2.0,
            "angry": 1.0,
            "surprise": 3.0,
            "fear": 1.0,
            "disgust": 1.0,
            "neutral": 2.0,
        }
        level, score = compute_engagement(scores)
        assert level == "engaged"
        assert score > 0.5

    def test_neutral_face_is_passive(self):
        scores = {
            "happy": 5.0,
            "sad": 5.0,
            "angry": 2.0,
            "surprise": 3.0,
            "fear": 2.0,
            "disgust": 3.0,
            "neutral": 80.0,
        }
        level, score = compute_engagement(scores)
        assert level == "passive"

    def test_sad_face_is_anxious(self):
        scores = {
            "happy": 2.0,
            "sad": 60.0,
            "angry": 5.0,
            "surprise": 1.0,
            "fear": 25.0,
            "disgust": 2.0,
            "neutral": 5.0,
        }
        level, score = compute_engagement(scores)
        assert level == "anxious"

    def test_angry_face_is_disruptive(self):
        scores = {
            "happy": 2.0,
            "sad": 3.0,
            "angry": 70.0,
            "surprise": 2.0,
            "fear": 3.0,
            "disgust": 15.0,
            "neutral": 5.0,
        }
        level, score = compute_engagement(scores)
        assert level == "disruptive"

    def test_mixed_signals_is_confused(self):
        scores = {
            "happy": 20.0,
            "sad": 15.0,
            "angry": 10.0,
            "surprise": 15.0,
            "fear": 10.0,
            "disgust": 10.0,
            "neutral": 20.0,
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


class TestEmotionAnalyzer:
    @patch("services.emotion_analyzer.DeepFace.analyze")
    def test_analyze_returns_faces(self, mock_analyze):
        mock_analyze.return_value = [
            {
                "region": {"x": 10, "y": 20, "w": 100, "h": 100},
                "emotion": {
                    "happy": 70.0,
                    "sad": 5.0,
                    "angry": 3.0,
                    "surprise": 10.0,
                    "fear": 2.0,
                    "disgust": 2.0,
                    "neutral": 8.0,
                },
                "dominant_emotion": "happy",
            }
        ]

        # 1x1 red pixel JPEG
        import io
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (48, 48), (255, 0, 0)).save(buf, format="JPEG")
        image_bytes = buf.getvalue()

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_image(image_bytes)

        assert isinstance(result, AnalysisResult)
        assert len(result.faces) == 1
        assert result.faces[0].dominant_emotion == "happy"
        assert result.faces[0].engagement_level == "engaged"
        assert result.processing_ms >= 0

    @patch("services.emotion_analyzer.DeepFace.analyze")
    def test_analyze_no_faces(self, mock_analyze):
        mock_analyze.return_value = []

        import io
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (48, 48), (0, 0, 0)).save(buf, format="JPEG")

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_image(buf.getvalue())

        assert result.faces == []

    @patch("services.emotion_analyzer.DeepFace.analyze")
    def test_analyze_handles_exception(self, mock_analyze):
        mock_analyze.side_effect = ValueError("No face detected")

        import io
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (48, 48), (0, 0, 0)).save(buf, format="JPEG")

        analyzer = EmotionAnalyzer()
        result = analyzer.analyze_image(buf.getvalue())

        assert result.faces == []
        assert result.processing_ms >= 0
