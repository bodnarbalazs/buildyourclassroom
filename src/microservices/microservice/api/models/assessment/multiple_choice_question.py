from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from api.models.assessment.difficulty import Difficulty
from api.models.assessment.question_type import QuestionType


class MultipleChoiceQuestion(BaseModel):
    question_type: Literal[QuestionType.MULTIPLE_CHOICE] = QuestionType.MULTIPLE_CHOICE
    question_text: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str
    explanation: str
    difficulty: Difficulty
