from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from api.models.agenda.energizer_element import EnergizerElement
from api.models.agenda.game_challenge_element import GameChallengeElement
from api.models.agenda.group_activity_element import GroupActivityElement
from api.models.agenda.individual_support_element import IndividualSupportElement
from api.models.agenda.lecture_element import LectureElement
from api.models.agenda.targeted_check_element import TargetedCheckElement

SectionElement = Annotated[
    LectureElement
    | TargetedCheckElement
    | GroupActivityElement
    | IndividualSupportElement
    | EnergizerElement
    | GameChallengeElement,
    Field(discriminator="element_type"),
]


class AgendaSection(BaseModel):
    order: int
    title: str
    description: str
    start_minute: int = Field(ge=1)
    duration_minutes: int = Field(ge=1)
    learning_objectives: list[str]
    element: SectionElement
