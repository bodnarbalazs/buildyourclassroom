from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from api.models.assessment.test_type import TestType


class AssessmentMetadata(BaseModel):
    title: str
    subject: str
    generated_from: str
    assessment_type: TestType
    total_questions: int
    created_at: datetime
