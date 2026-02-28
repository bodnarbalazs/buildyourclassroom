from __future__ import annotations

from pydantic import BaseModel

from api.models.simulation.student_snapshot import StudentSnapshot


class TickSnapshot(BaseModel):
    cycle: int
    students: list[StudentSnapshot]
    avg_engagement: float
