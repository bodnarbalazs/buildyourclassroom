from __future__ import annotations

import tempfile
import time
from pathlib import Path

import structlog
from fastapi import APIRouter, Form, HTTPException, UploadFile
from openai import OpenAIError

from api.models.assessment import AssessmentBundle, GenerateAssessmentFromTranscriptRequest
from services.assessment_generator import AssessmentGenerationError, AssessmentGenerator
from services.transcription_service import (
    SUPPORTED_EXTENSIONS,
    TranscriptionError,
    TranscriptionService,
)

router = APIRouter()
logger = structlog.get_logger()

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB

_transcription_service: TranscriptionService | None = None
_assessment_generator: AssessmentGenerator | None = None


def _get_transcription_service() -> TranscriptionService:
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service


def _get_assessment_generator() -> AssessmentGenerator:
    global _assessment_generator
    if _assessment_generator is None:
        _assessment_generator = AssessmentGenerator()
    return _assessment_generator


@router.post("/generate-assessments", response_model=AssessmentBundle)
async def generate_assessments(
    file: UploadFile,
    subject: str | None = Form(default=None),
    target_audience: str | None = Form(default=None),
    additional_instructions: str | None = Form(default=None),
) -> AssessmentBundle:
    log = logger.bind(filename=file.filename)

    # Validate extension
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    # Read and check size
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Save to temp file for processing
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp_path = Path(tmp.name)
    try:
        tmp.write(content)
        tmp.close()

        # Stage 1: Transcription
        log.info("transcription_started")
        t0 = time.monotonic()
        try:
            transcription_svc = _get_transcription_service()
            result = await transcription_svc.transcribe_file(tmp_path)
        except TranscriptionError as exc:
            log.error("transcription_failed", error=str(exc))
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except OpenAIError as exc:
            log.error("whisper_service_error", error=str(exc))
            raise HTTPException(
                status_code=502, detail=f"Whisper service error: {exc}"
            ) from exc

        transcript = result.text
        transcription_duration = time.monotonic() - t0
        log.info(
            "transcription_completed",
            duration_s=round(transcription_duration, 2),
            transcript_length=len(transcript),
        )

        if not transcript.strip():
            raise HTTPException(status_code=400, detail="Transcription produced empty result")

        # Stage 2: Assessment generation
        return await _generate_from_transcript(
            transcript=transcript,
            subject=subject,
            target_audience=target_audience,
            additional_instructions=additional_instructions,
            generated_from=filename,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/generate-assessments/from-transcript", response_model=AssessmentBundle)
async def generate_assessments_from_transcript(
    body: GenerateAssessmentFromTranscriptRequest,
) -> AssessmentBundle:
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript is empty")

    return await _generate_from_transcript(
        transcript=body.transcript,
        subject=body.subject,
        target_audience=body.target_audience,
        additional_instructions=body.additional_instructions,
        generated_from="direct_transcript",
    )


async def _generate_from_transcript(
    transcript: str,
    subject: str | None,
    target_audience: str | None,
    additional_instructions: str | None,
    generated_from: str,
) -> AssessmentBundle:
    log = logger.bind(generated_from=generated_from)
    log.info("assessment_generation_started")

    try:
        generator = _get_assessment_generator()
        bundle = await generator.generate(
            transcript=transcript,
            subject=subject,
            target_audience=target_audience,
            additional_instructions=additional_instructions,
            generated_from=generated_from,
        )
    except AssessmentGenerationError as exc:
        log.error("assessment_generation_failed", error=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except OpenAIError as exc:
        log.error("azure_openai_error", error=str(exc))
        raise HTTPException(
            status_code=502, detail=f"Azure OpenAI service error: {exc}"
        ) from exc

    log.info("assessment_generation_completed")
    return bundle
