from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    title: str
    user_id: str | None = None


class SessionResponse(BaseModel):
    id: UUID
    title: str
    user_id: str | None
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FaceResultResponse(BaseModel):
    face_index: int
    bbox: dict
    dominant_emotion: str
    emotion_scores: dict[str, float]
    engagement_level: str
    engagement_score: float


class SnapshotResultResponse(BaseModel):
    snapshot_id: UUID
    session_id: UUID
    captured_at: datetime
    face_count: int
    processing_ms: float
    faces: list[FaceResultResponse]


class SessionSummaryResponse(BaseModel):
    session_id: UUID
    title: str
    duration_seconds: float | None
    total_snapshots: int
    total_faces_detected: int
    avg_engagement_score: float
    engagement_distribution: dict[str, int]
    emotion_distribution: dict[str, int]


class TimelineBucket(BaseModel):
    bucket_start: datetime
    bucket_end: datetime
    avg_engagement_score: float
    dominant_emotion: str
    face_count: int
