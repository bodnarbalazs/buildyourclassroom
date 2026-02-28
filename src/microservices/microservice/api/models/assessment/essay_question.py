from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from api.models.assessment.difficulty import Difficulty
from api.models.assessment.question_type import QuestionType


class EssayQuestion(BaseModel):
    question_type: Literal[QuestionType.ESSAY] = QuestionType.ESSAY
    question_text: str
    correct_answer: str
    explanation: str
    difficulty: Difficulty
    grading_rubric: list[str] = Field(min_length=1)
