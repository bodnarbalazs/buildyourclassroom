from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.emotion_orm import FaceResult, Session, Snapshot
from services.emotion_analyzer import FaceAnalysis


class EmotionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, title: str, user_id: str | None = None) -> Session:
        session = Session(title=title, user_id=user_id)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: uuid.UUID) -> Session | None:
        return await self.db.get(Session, session_id)

    async def list_sessions(self, skip: int = 0, limit: int = 20) -> list[Session]:
        result = await self.db.execute(
            select(Session).order_by(Session.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def end_session(self, session_id: uuid.UUID) -> Session | None:
        session = await self.db.get(Session, session_id)
        if not session:
            return None
        session.ended_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def save_snapshot(
        self,
        session_id: uuid.UUID,
        faces: list[FaceAnalysis],
        processing_ms: float,
    ) -> Snapshot:
        snapshot = Snapshot(
            session_id=session_id,
            face_count=len(faces),
            processing_ms=processing_ms,
        )
        self.db.add(snapshot)
        await self.db.flush()

        for face in faces:
            self.db.add(
                FaceResult(
                    snapshot_id=snapshot.id,
                    face_index=face.face_index,
                    bbox_x=face.bbox_x,
                    bbox_y=face.bbox_y,
                    bbox_w=face.bbox_w,
                    bbox_h=face.bbox_h,
                    dominant_emotion=face.dominant_emotion,
                    emotion_scores=face.emotion_scores,
                    engagement_level=face.engagement_level,
                    engagement_score=face.engagement_score,
                )
            )

        await self.db.commit()
        result = await self.db.execute(
            select(Snapshot)
            .options(selectinload(Snapshot.face_results))
            .where(Snapshot.id == snapshot.id)
        )
        return result.scalar_one()

    async def get_session_summary(self, session_id: uuid.UUID) -> dict | None:
        session = await self.db.get(Session, session_id)
        if not session:
            return None

        snapshot_count = await self.db.scalar(
            select(func.count()).where(Snapshot.session_id == session_id)
        )

        faces_result = await self.db.execute(
            select(FaceResult).join(Snapshot).where(Snapshot.session_id == session_id)
        )
        all_faces = list(faces_result.scalars().all())

        total_faces = len(all_faces)
        avg_engagement = (
            sum(f.engagement_score for f in all_faces) / total_faces if total_faces else 0.0
        )

        engagement_counts = Counter(f.engagement_level for f in all_faces)
        emotion_counts = Counter(f.dominant_emotion for f in all_faces)

        duration = None
        if session.ended_at and session.started_at:
            duration = (session.ended_at - session.started_at).total_seconds()

        return {
            "session_id": session.id,
            "title": session.title,
            "duration_seconds": duration,
            "total_snapshots": snapshot_count or 0,
            "total_faces_detected": total_faces,
            "avg_engagement_score": round(avg_engagement, 4),
            "engagement_distribution": dict(engagement_counts),
            "emotion_distribution": dict(emotion_counts),
        }

    async def get_timeline(
        self, session_id: uuid.UUID, interval_seconds: int = 10
    ) -> list[dict]:
        session = await self.db.get(Session, session_id)
        if not session:
            return []

        snapshots_result = await self.db.execute(
            select(Snapshot)
            .options(selectinload(Snapshot.face_results))
            .where(Snapshot.session_id == session_id)
            .order_by(Snapshot.captured_at)
        )
        snapshots = list(snapshots_result.scalars().all())
        if not snapshots:
            return []

        interval = timedelta(seconds=interval_seconds)
        bucket_start = snapshots[0].captured_at
        buckets: list[dict] = []
        current_faces: list[FaceResult] = []

        for snap in snapshots:
            while snap.captured_at >= bucket_start + interval:
                buckets.append(_build_bucket(bucket_start, interval, current_faces))
                bucket_start += interval
                current_faces = []
            current_faces.extend(snap.face_results)

        if current_faces:
            buckets.append(_build_bucket(bucket_start, interval, current_faces))

        return buckets


def _build_bucket(
    start: datetime, interval: timedelta, faces: list[FaceResult]
) -> dict:
    if not faces:
        return {
            "bucket_start": start,
            "bucket_end": start + interval,
            "avg_engagement_score": 0.0,
            "dominant_emotion": "neutral",
            "face_count": 0,
        }

    avg_score = sum(f.engagement_score for f in faces) / len(faces)
    emotion_counts = Counter(f.dominant_emotion for f in faces)
    dominant = emotion_counts.most_common(1)[0][0]

    return {
        "bucket_start": start,
        "bucket_end": start + interval,
        "avg_engagement_score": round(avg_score, 4),
        "dominant_emotion": dominant,
        "face_count": len(faces),
    }
