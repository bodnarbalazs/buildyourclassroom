from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from api.models.assessment.assessment_metadata import AssessmentMetadata
from api.models.assessment.bloom_level import BloomLevel
from api.models.assessment.fill_in_the_blank_question import FillInTheBlankQuestion
from api.models.assessment.matching_question import MatchingQuestion
from api.models.assessment.multiple_choice_question import MultipleChoiceQuestion
from api.models.assessment.short_answer_question import ShortAnswerQuestion
from api.models.assessment.true_false_question import TrueFalseQuestion

PracticeTestBaseQuestion = Annotated[
    MultipleChoiceQuestion | TrueFalseQuestion | ShortAnswerQuestion
    | FillInTheBlankQuestion | MatchingQuestion,
    Field(discriminator="question_type"),
]


class PracticeTestQuestion(BaseModel):
    base: PracticeTestBaseQuestion
    topic_tag: str
    bloom_level: BloomLevel


class PracticeTestSection(BaseModel):
    section_title: str
    questions: list[PracticeTestQuestion] = Field(min_length=1)


class PracticeTest(AssessmentMetadata):
    sections: list[PracticeTestSection] = Field(min_length=1)
