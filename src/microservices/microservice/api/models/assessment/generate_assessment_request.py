from __future__ import annotations

from pydantic import BaseModel


class GenerateAssessmentFromTranscriptRequest(BaseModel):
    transcript: str
    subject: str | None = None
    target_audience: str | None = None
    additional_instructions: str | None = None
