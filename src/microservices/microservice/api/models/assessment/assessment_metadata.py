from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AssessmentMetadata(BaseModel):
    title: str
    subject: str
    generated_from: str
    assessment_type: Literal["quick-quiz", "chapter-test", "midterm", "final-exam"]
    total_questions: int
    created_at: datetime
