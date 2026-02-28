from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from api.models.assessment.difficulty import Difficulty
from api.models.assessment.question_type import QuestionType


class TrueFalseQuestion(BaseModel):
    question_type: Literal[QuestionType.TRUE_FALSE] = QuestionType.TRUE_FALSE
    question_text: str
    correct_answer: bool
    explanation: str
    difficulty: Difficulty
