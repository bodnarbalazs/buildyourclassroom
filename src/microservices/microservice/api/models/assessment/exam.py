from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from api.models.assessment.assessment_metadata import AssessmentMetadata
from api.models.assessment.bloom_level import BloomLevel
from api.models.assessment.essay_question import EssayQuestion
from api.models.assessment.fill_in_the_blank_question import FillInTheBlankQuestion
from api.models.assessment.matching_question import MatchingQuestion
from api.models.assessment.multiple_choice_question import MultipleChoiceQuestion
from api.models.assessment.short_answer_question import ShortAnswerQuestion
from api.models.assessment.true_false_question import TrueFalseQuestion

ExamBaseQuestion = Annotated[
    MultipleChoiceQuestion | TrueFalseQuestion | ShortAnswerQuestion
    | FillInTheBlankQuestion | MatchingQuestion | EssayQuestion,
    Field(discriminator="question_type"),
]


class ExamQuestion(BaseModel):
    base: ExamBaseQuestion
    topic_tag: str
    bloom_level: BloomLevel
    points: int = Field(ge=1)


class ExamSection(BaseModel):
    section_title: str
    questions: list[ExamQuestion] = Field(min_length=1)


class Exam(AssessmentMetadata):
    sections: list[ExamSection] = Field(min_length=1)
    total_points: int = Field(ge=1)
    time_limit_minutes: int = Field(ge=1)
