from __future__ import annotations

from typing import Annotated

from pydantic import Field

from api.models.assessment.assessment_metadata import AssessmentMetadata
from api.models.assessment.fill_in_the_blank_question import FillInTheBlankQuestion
from api.models.assessment.multiple_choice_question import MultipleChoiceQuestion
from api.models.assessment.true_false_question import TrueFalseQuestion

QuizQuestion = Annotated[
    MultipleChoiceQuestion | TrueFalseQuestion | FillInTheBlankQuestion,
    Field(discriminator="question_type"),
]


class Quiz(AssessmentMetadata):
    questions: list[QuizQuestion] = Field(min_length=5, max_length=10)
