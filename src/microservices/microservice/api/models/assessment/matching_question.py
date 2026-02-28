from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from api.models.assessment.difficulty import Difficulty
from api.models.assessment.question_type import QuestionType


class MatchingPair(BaseModel):
    left: str
    right: str


class MatchingQuestion(BaseModel):
    question_type: Literal[QuestionType.MATCHING] = QuestionType.MATCHING
    question_text: str
    pairs: list[MatchingPair] = Field(min_length=2)
    correct_answer: str
    explanation: str
    difficulty: Difficulty
