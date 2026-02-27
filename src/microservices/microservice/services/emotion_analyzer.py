from __future__ import annotations

import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _crop_face(frame: np.ndarray, region: dict, padding_pct: float = 0.15) -> np.ndarray:
    """Crop a face region from the frame with padding, clamped to image bounds."""
    h_img, w_img = frame.shape[:2]
    x, y, w, h = region["x"], region["y"], region["w"], region["h"]
    pad_x = int(w * padding_pct)
    pad_y = int(h * padding_pct)
    x1 = max(x - pad_x, 0)
    y1 = max(y - pad_y, 0)
    x2 = min(x + w + pad_x, w_img)
    y2 = min(y + h + pad_y, h_img)
    return frame[y1:y2, x1:x2]


class EmotionAnalyzer:
    """Wraps deepface for emotion detection. Intended as a singleton."""

    _MAX_WORKERS = 4

    def warm_up(self) -> None:
        """Force model download/load at startup instead of first request."""
        dummy = np.zeros((48, 48, 3), dtype=np.uint8)
        try:
            DeepFace.analyze(
                dummy,
                actions=["emotion"],
                detector_backend="mtcnn",
                enforce_detection=False,
                silent=True,
            )
        except Exception:
            pass

    def _analyze_single_face(
        self, face_crop: np.ndarray, face_index: int, bbox: dict
    ) -> FaceAnalysis:
        """Run emotion analysis on a single pre-cropped face image."""
        result = DeepFace.analyze(
            face_crop,
            actions=["emotion"],
            detector_backend="skip",
            enforce_detection=False,
            silent=True,
        )
        face_data = result[0] if isinstance(result, list) else result
        emotions = {k: float(v) for k, v in face_data.get("emotion", {}).items()}
        dominant = face_data.get("dominant_emotion", "neutral")
        level, score = compute_engagement(emotions)
        return FaceAnalysis(
            face_index=face_index,
            bbox_x=bbox["x"],
            bbox_y=bbox["y"],
            bbox_w=bbox["w"],
            bbox_h=bbox["h"],
            dominant_emotion=dominant,
            emotion_scores=emotions,
            engagement_level=level,
            engagement_score=score,
        )

    def analyze_image(self, image_bytes: bytes) -> AnalysisResult:
        """Decode image bytes and run emotion analysis on all detected faces.

        Uses a two-stage pipeline: detect faces first, then analyze each
        cropped face in parallel for better performance with many faces.
        """
        start = time.perf_counter()

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        try:
            return self._analyze_two_stage(frame, start)
        except Exception:
            elapsed = (time.perf_counter() - start) * 1000
            return AnalysisResult(faces=[], processing_ms=round(elapsed, 2))

    def _analyze_two_stage(self, frame: np.ndarray, start: float) -> AnalysisResult:
        """Detect faces, crop each, then analyze emotions in parallel."""
        # Stage 1: detect all face bounding boxes
        detected = DeepFace.extract_faces(
            frame,
            detector_backend="mtcnn",
            enforce_detection=False,
        )

        if not detected:
            elapsed = (time.perf_counter() - start) * 1000
            return AnalysisResult(faces=[], processing_ms=round(elapsed, 2))

        # Build (index, crop, bbox) tuples
        jobs: list[tuple[int, np.ndarray, dict]] = []
        for i, det in enumerate(detected):
            region = det.get("facial_area", {})
            bbox = {
                "x": region.get("x", 0),
                "y": region.get("y", 0),
                "w": region.get("w", 0),
                "h": region.get("h", 0),
            }
            if bbox["w"] <= 0 or bbox["h"] <= 0:
                continue
            crop = _crop_face(frame, bbox)
            jobs.append((i, crop, bbox))

        if not jobs:
            elapsed = (time.perf_counter() - start) * 1000
            return AnalysisResult(faces=[], processing_ms=round(elapsed, 2))

        # Stage 2: analyze each face in parallel
        faces: list[FaceAnalysis] = []
        workers = min(len(jobs), self._MAX_WORKERS)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(self._analyze_single_face, crop, idx, bbox): idx
                for idx, crop, bbox in jobs
            }
            for future in as_completed(futures):
                try:
                    faces.append(future.result())
                except Exception:
                    pass

        faces.sort(key=lambda f: f.face_index)
        elapsed = (time.perf_counter() - start) * 1000
        return AnalysisResult(faces=faces, processing_ms=round(elapsed, 2))
