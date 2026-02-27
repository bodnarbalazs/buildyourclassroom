from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, model_validator

from api.models.agenda.lesson_element_type import ELEMENT_TYPE_TO_CA_ACTION, LessonElementType

_CA_ACTION = ELEMENT_TYPE_TO_CA_ACTION[LessonElementType.ENERGIZER]


class EnergizerElement(BaseModel):
    element_type: Literal[LessonElementType.ENERGIZER] = LessonElementType.ENERGIZER
    ca_action: int = _CA_ACTION
    pedagogical_rationale: str
    energizer_type: Literal["humor", "anecdote", "fun_fact", "video_clip", "brain_break"]
    description: str

    @model_validator(mode="before")
    @classmethod
    def set_ca_action(cls, data: dict) -> dict:
        if isinstance(data, dict):
            data["ca_action"] = _CA_ACTION
        return data
