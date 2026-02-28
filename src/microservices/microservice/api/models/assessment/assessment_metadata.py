from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AssessmentMetadata(BaseModel):
    title: str
    subject: str
    generated_from: str
    assessment_type: Literal["quiz", "practice_test", "exam"]
    total_questions: int
    created_at: datetime
