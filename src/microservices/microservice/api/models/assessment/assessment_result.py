from __future__ import annotations

from typing import Annotated, Union

from pydantic import BaseModel, Field

from api.models.assessment.exam import Exam
from api.models.assessment.practice_test import PracticeTest
from api.models.assessment.quiz import Quiz


class AssessmentResult(BaseModel):
    transcript_summary: str
    assessment: Annotated[
        Union[Quiz, PracticeTest, Exam],
        Field(discriminator="assessment_type"),
    ]
