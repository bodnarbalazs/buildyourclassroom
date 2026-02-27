from pydantic import BaseModel, Field


class GenerateAgendaRequest(BaseModel):
    subject: str
    topic: str
    target_audience: str
    duration_minutes: int = Field(ge=1)
    additional_instructions: str | None = None
