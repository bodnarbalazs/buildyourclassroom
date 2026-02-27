from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from openai import OpenAIError

from api.models.agenda import GenerateAgendaRequest, GenerateAgendaResponse
from services.agenda_generator import AgendaGenerationError, AgendaGenerator

router = APIRouter()
logger = structlog.get_logger()

_generator: AgendaGenerator | None = None


def _get_generator() -> AgendaGenerator:
    global _generator
    if _generator is None:
        _generator = AgendaGenerator()
    return _generator


@router.post("/generate-agenda", response_model=GenerateAgendaResponse)
async def generate_agenda(body: GenerateAgendaRequest) -> GenerateAgendaResponse:
    log = logger.bind(subject=body.subject, topic=body.topic)
    log.info("agenda_generation_started", duration=body.duration_minutes)

    try:
        generator = _get_generator()
        agenda = await generator.generate(
            subject=body.subject,
            topic=body.topic,
            target_audience=body.target_audience,
            duration_minutes=body.duration_minutes,
            additional_instructions=body.additional_instructions,
        )
    except AgendaGenerationError as exc:
        log.error("agenda_generation_failed", error=str(exc))
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except OpenAIError as exc:
        log.error("azure_openai_error", error=str(exc))
        raise HTTPException(
            status_code=502, detail=f"Azure OpenAI service error: {exc}"
        ) from exc

    log.info("agenda_generation_completed", sections=len(agenda.sections))

    return GenerateAgendaResponse(**agenda.model_dump(), ca_schedule=agenda.to_ca_schedule())
