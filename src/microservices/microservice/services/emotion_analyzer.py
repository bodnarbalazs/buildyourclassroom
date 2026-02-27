from __future__ import annotations

import io
import time
from dataclasses import dataclass

import cv2
import numpy as np
from deepface import DeepFace
from PIL import Image

# How conducive each engagement level is to learning (used as the score)
LEVEL_QUALITY: dict[str, float] = {
    "engaged": 1.0,
    "passive": 0.5,
    "confused": 0.3,
    "anxious": 0.2,
    "disruptive": 0.1,
}

# Minimum combined percentage for a signal group to be considered dominant
_DOMINANCE_THRESHOLD = 40.0


@dataclass
class FaceAnalysis:
    face_index: int
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    dominant_emotion: str
    emotion_scores: dict[str, float]
    engagement_level: str
    engagement_score: float


@dataclass
class AnalysisResult:
    faces: list[FaceAnalysis]
    processing_ms: float


def compute_engagement(emotion_scores: dict[str, float]) -> tuple[str, float]:
    """Map deepface emotion percentages to an engagement level and 0-1 score.

    Levels: engaged, passive, confused, anxious, disruptive.
    Score reflects how conducive the detected state is to learning.
    """
    signals = {
        "engaged": (
            emotion_scores.get("happy", 0.0) + emotion_scores.get("surprise", 0.0)
        ),
        "passive": emotion_scores.get("neutral", 0.0),
        "anxious": (
            emotion_scores.get("sad", 0.0) + emotion_scores.get("fear", 0.0)
        ),
        "disruptive": (
            emotion_scores.get("angry", 0.0) + emotion_scores.get("disgust", 0.0)
        ),
    }

    top_level = max(signals, key=signals.get)
    top_pct = signals[top_level]

    # No clear dominant signal → student looks confused
    level = "confused" if top_pct < _DOMINANCE_THRESHOLD else top_level

    quality = LEVEL_QUALITY[level]
    score = quality * min(top_pct / 100.0, 1.0) if level != "confused" else quality

    return level, round(min(max(score, 0.0), 1.0), 4)


class EmotionAnalyzer:
    """Wraps deepface for emotion detection. Intended as a singleton."""

    def warm_up(self) -> None:
        """Force model download/load at startup instead of first request."""
        dummy = np.zeros((48, 48, 3), dtype=np.uint8)
        try:
            DeepFace.analyze(
                dummy,
                actions=["emotion"],
                detector_backend="opencv",
                enforce_detection=False,
                silent=True,
            )
        except Exception:
            pass

    def analyze_image(self, image_bytes: bytes) -> AnalysisResult:
        """Decode image bytes and run emotion analysis on all detected faces."""
        start = time.perf_counter()

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        try:
            results = DeepFace.analyze(
                frame,
                actions=["emotion"],
                detector_backend="opencv",
                enforce_detection=False,
                silent=True,
            )
        except Exception:
            elapsed = (time.perf_counter() - start) * 1000
            return AnalysisResult(faces=[], processing_ms=round(elapsed, 2))

        if isinstance(results, dict):
            results = [results]

        faces: list[FaceAnalysis] = []
        for i, face_data in enumerate(results):
            region = face_data.get("region", {})
            emotions = {k: float(v) for k, v in face_data.get("emotion", {}).items()}
            dominant = face_data.get("dominant_emotion", "neutral")
            level, score = compute_engagement(emotions)

            faces.append(
                FaceAnalysis(
                    face_index=i,
                    bbox_x=region.get("x", 0),
                    bbox_y=region.get("y", 0),
                    bbox_w=region.get("w", 0),
                    bbox_h=region.get("h", 0),
                    dominant_emotion=dominant,
                    emotion_scores=emotions,
                    engagement_level=level,
                    engagement_score=score,
                )
            )

        elapsed = (time.perf_counter() - start) * 1000
        return AnalysisResult(faces=faces, processing_ms=round(elapsed, 2))
