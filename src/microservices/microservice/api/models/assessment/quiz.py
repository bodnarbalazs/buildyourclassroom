from __future__ import annotations

from typing import Annotated

from pydantic import Field

from api.models.assessment.assessment_metadata import AssessmentMetadata
from api.models.assessment.essay_question import EssayQuestion
from api.models.assessment.multiple_choice_question import MultipleChoiceQuestion
from api.models.assessment.short_answer_question import ShortAnswerQuestion
from api.models.assessment.true_false_question import TrueFalseQuestion

QuizQuestion = Annotated[
    MultipleChoiceQuestion | TrueFalseQuestion | ShortAnswerQuestion | EssayQuestion,
    Field(discriminator="question_type"),
]


class Quiz(AssessmentMetadata):
    questions: list[QuizQuestion] = Field(min_length=1)
