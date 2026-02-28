from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.emotion_schemas import (
    CreateSessionRequest,
    FaceResultResponse,
    SessionResponse,
    SessionSummaryResponse,
    SnapshotResultResponse,
    TimelineBucket,
)
from services.emotion_analyzer import EmotionAnalyzer
from services.emotion_repository import EmotionRepository
from shared.database import get_db

router = APIRouter()

_analyzer = EmotionAnalyzer()


def get_repo(db: AsyncSession = Depends(get_db)) -> EmotionRepository:
    return EmotionRepository(db)


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    body: CreateSessionRequest,
    repo: EmotionRepository = Depends(get_repo),
):
    session = await repo.create_session(title=body.title, user_id=body.user_id)
    return session


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 20,
    repo: EmotionRepository = Depends(get_repo),
):
    return await repo.list_sessions(skip=skip, limit=limit)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    repo: EmotionRepository = Depends(get_repo),
):
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: UUID,
    repo: EmotionRepository = Depends(get_repo),
):
    session = await repo.end_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/snapshots", response_model=SnapshotResultResponse)
async def upload_snapshot(
    session_id: UUID,
    file: UploadFile,
    repo: EmotionRepository = Depends(get_repo),
):
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.ended_at:
        raise HTTPException(status_code=400, detail="Session already ended")

    image_bytes = await file.read()
    result = await asyncio.to_thread(_analyzer.analyze_image, image_bytes)

    snapshot = await repo.save_snapshot(
        session_id=session_id,
        faces=result.faces,
        processing_ms=result.processing_ms,
    )

    return SnapshotResultResponse(
        snapshot_id=snapshot.id,
        session_id=snapshot.session_id,
        captured_at=snapshot.captured_at,
        face_count=snapshot.face_count,
        processing_ms=snapshot.processing_ms,
        faces=[
            FaceResultResponse(
                face_index=fr.face_index,
                bbox={"x": fr.bbox_x, "y": fr.bbox_y, "w": fr.bbox_w, "h": fr.bbox_h},
                dominant_emotion=fr.dominant_emotion,
                emotion_scores=fr.emotion_scores,
                engagement_level=fr.engagement_level,
                engagement_score=fr.engagement_score,
            )
            for fr in snapshot.face_results
        ],
    )


@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(
    session_id: UUID,
    repo: EmotionRepository = Depends(get_repo),
):
    summary = await repo.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary


@router.get("/sessions/{session_id}/timeline", response_model=list[TimelineBucket])
async def get_session_timeline(
    session_id: UUID,
    interval_seconds: int = 10,
    repo: EmotionRepository = Depends(get_repo),
):
    return await repo.get_timeline(session_id, interval_seconds=interval_seconds)
