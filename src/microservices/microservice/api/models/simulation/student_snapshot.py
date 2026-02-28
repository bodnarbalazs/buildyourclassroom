from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Emotion = Literal["engaged", "passive", "anxious", "confused", "disruptive"]


class StudentSnapshot(BaseModel):
    id: int
    engagement: int
    emotion: Emotion
