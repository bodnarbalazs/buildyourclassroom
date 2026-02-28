from __future__ import annotations

from pydantic import BaseModel

from api.models.assessment.exam import Exam
from api.models.assessment.practice_test import PracticeTest
from api.models.assessment.quiz import Quiz


class AssessmentResult(BaseModel):
    transcript_summary: str
    assessment: Quiz | Exam | PracticeTest
