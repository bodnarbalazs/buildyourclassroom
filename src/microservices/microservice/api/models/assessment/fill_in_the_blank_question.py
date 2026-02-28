from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from api.models.assessment.difficulty import Difficulty
from api.models.assessment.question_type import QuestionType


class FillInTheBlankQuestion(BaseModel):
    question_type: Literal[QuestionType.FILL_IN_THE_BLANK] = QuestionType.FILL_IN_THE_BLANK
    question_text: str
    correct_answer: str
    explanation: str
    difficulty: Difficulty
