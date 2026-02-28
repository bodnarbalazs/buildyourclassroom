from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from api.models.assessment.difficulty import Difficulty
from api.models.assessment.question_type import QuestionType


class ShortAnswerQuestion(BaseModel):
    question_type: Literal[QuestionType.SHORT_ANSWER] = QuestionType.SHORT_ANSWER
    question_text: str
    correct_answer: str
    explanation: str
    difficulty: Difficulty
