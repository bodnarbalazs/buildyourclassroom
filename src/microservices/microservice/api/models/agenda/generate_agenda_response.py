from __future__ import annotations

from api.models.agenda.lesson_agenda import LessonAgenda


class GenerateAgendaResponse(LessonAgenda):
    ca_schedule: list[dict]
