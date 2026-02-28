from __future__ import annotations

from pydantic import BaseModel, Field


class ScheduleEvent(BaseModel):
    time: int = Field(ge=1)
    action: int = Field(ge=1, le=6)
    duration: int = Field(default=0, ge=0)


class SimulateRequest(BaseModel):
    ca_schedule: list[ScheduleEvent]
    rows: int = Field(default=5, ge=1, le=20)
    cols: int = Field(default=6, ge=1, le=20)
    cycles: int = Field(default=45, ge=1, le=120)
    max_engagement: int = Field(default=5, ge=1, le=10)
    seed: int | None = None
