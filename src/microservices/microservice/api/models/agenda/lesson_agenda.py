from __future__ import annotations

from pydantic import BaseModel, Field

from api.models.agenda.agenda_section import AgendaSection


class LessonAgenda(BaseModel):
    lesson_title: str
    subject: str
    target_audience: str
    total_duration_minutes: int = Field(ge=1)
    overall_objectives: list[str]
    sections: list[AgendaSection] = Field(min_length=1)
    summary: str

    def to_ca_schedule(self) -> list[dict]:
        schedule: list[dict] = []
        for section in self.sections:
            entry: dict = {
                "time": section.start_minute,
                "action": section.element.ca_action,
            }
            if section.element.ca_action in (3, 6):
                entry["duration"] = section.duration_minutes
            schedule.append(entry)
        schedule.sort(key=lambda e: e["time"])
        return schedule
