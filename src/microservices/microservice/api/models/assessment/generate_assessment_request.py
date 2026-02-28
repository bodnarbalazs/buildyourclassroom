from __future__ import annotations

from pydantic import BaseModel, Field

from api.models.assessment.difficulty import Difficulty
from api.models.assessment.language import Language
from api.models.assessment.question_type import QuestionType
from api.models.assessment.test_type import TestType


class GenerateAssessmentFromTranscriptRequest(BaseModel):
    transcript: str
    test_type: TestType = TestType.CHAPTER_TEST
    difficulty: Difficulty = Difficulty.MEDIUM
    num_questions: int = Field(default=10, ge=1, le=100)
    question_types: list[QuestionType] = [QuestionType.MULTIPLE_CHOICE]
    language: Language = Language.ENGLISH
    subject: str | None = None
    target_audience: str | None = None
    additional_instructions: str | None = None
