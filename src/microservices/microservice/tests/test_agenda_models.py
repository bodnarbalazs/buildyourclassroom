"""Tests for agenda models: discriminated union, ca_action auto-population, to_ca_schedule."""
from api.models.agenda import (
    AgendaSection,
    EnergizerElement,
    GameChallengeElement,
    GroupActivityElement,
    IndividualSupportElement,
    LectureElement,
    LessonAgenda,
    TargetedCheckElement,
)
from api.models.agenda.lesson_element_type import ELEMENT_TYPE_TO_CA_ACTION, LessonElementType


def _lecture(**overrides):
    defaults = {
        "element_type": "LECTURE",
        "pedagogical_rationale": "intro",
        "key_points": ["a"],
        "instructor_notes": "n",
    }
    return {**defaults, **overrides}


def _group_activity(**overrides):
    defaults = {
        "element_type": "GROUP_ACTIVITY",
        "pedagogical_rationale": "collab",
        "activity_title": "t",
        "instructions": "i",
        "group_size": 4,
        "materials_needed": [],
    }
    return {**defaults, **overrides}


def _game_challenge(**overrides):
    defaults = {
        "element_type": "GAME_CHALLENGE",
        "pedagogical_rationale": "energy",
        "game_title": "quiz",
        "rules": "r",
        "team_based": True,
    }
    return {**defaults, **overrides}


def _energizer(**overrides):
    defaults = {
        "element_type": "ENERGIZER",
        "pedagogical_rationale": "break",
        "energizer_type": "humor",
        "description": "joke",
    }
    return {**defaults, **overrides}


def _targeted_check(**overrides):
    defaults = {
        "element_type": "TARGETED_CHECK",
        "pedagogical_rationale": "check",
        "focus_area": "math",
        "questions": ["q1"],
    }
    return {**defaults, **overrides}


def _individual_support(**overrides):
    defaults = {
        "element_type": "INDIVIDUAL_SUPPORT",
        "pedagogical_rationale": "help",
        "support_focus": "reading",
        "follow_up": "practice",
    }
    return {**defaults, **overrides}


def _section(order, start, duration, element_data):
    return {
        "order": order,
        "title": f"Section {order}",
        "description": "d",
        "start_minute": start,
        "duration_minutes": duration,
        "learning_objectives": ["obj"],
        "element": element_data,
    }


def _agenda_data(sections_data):
    return {
        "lesson_title": "Test",
        "subject": "Math",
        "target_audience": "Grade 5",
        "total_duration_minutes": sum(s["duration_minutes"] for s in sections_data),
        "overall_objectives": ["learn"],
        "sections": sections_data,
        "summary": "done",
    }


class TestDiscriminatedUnion:
    def test_deserializes_lecture(self):
        section = AgendaSection.model_validate(
            _section(1, 1, 10, _lecture())
        )
        assert isinstance(section.element, LectureElement)

    def test_deserializes_targeted_check(self):
        section = AgendaSection.model_validate(
            _section(1, 1, 5, _targeted_check())
        )
        assert isinstance(section.element, TargetedCheckElement)

    def test_deserializes_group_activity(self):
        section = AgendaSection.model_validate(
            _section(1, 1, 15, _group_activity())
        )
        assert isinstance(section.element, GroupActivityElement)

    def test_deserializes_individual_support(self):
        section = AgendaSection.model_validate(
            _section(1, 1, 5, _individual_support())
        )
        assert isinstance(section.element, IndividualSupportElement)

    def test_deserializes_energizer(self):
        section = AgendaSection.model_validate(
            _section(1, 1, 3, _energizer())
        )
        assert isinstance(section.element, EnergizerElement)

    def test_deserializes_game_challenge(self):
        section = AgendaSection.model_validate(
            _section(1, 1, 10, _game_challenge())
        )
        assert isinstance(section.element, GameChallengeElement)


class TestCaActionAutoPopulation:
    """ca_action is always set from ELEMENT_TYPE_TO_CA_ACTION, even if input omits or overrides it."""

    def test_lecture_ca_action(self):
        elem = LectureElement.model_validate(_lecture())
        assert elem.ca_action == ELEMENT_TYPE_TO_CA_ACTION[LessonElementType.LECTURE]

    def test_targeted_check_ca_action(self):
        elem = TargetedCheckElement.model_validate(_targeted_check())
        assert elem.ca_action == ELEMENT_TYPE_TO_CA_ACTION[LessonElementType.TARGETED_CHECK]

    def test_group_activity_ca_action(self):
        elem = GroupActivityElement.model_validate(_group_activity())
        assert elem.ca_action == ELEMENT_TYPE_TO_CA_ACTION[LessonElementType.GROUP_ACTIVITY]

    def test_individual_support_ca_action(self):
        elem = IndividualSupportElement.model_validate(_individual_support())
        assert elem.ca_action == ELEMENT_TYPE_TO_CA_ACTION[LessonElementType.INDIVIDUAL_SUPPORT]

    def test_energizer_ca_action(self):
        elem = EnergizerElement.model_validate(_energizer())
        assert elem.ca_action == ELEMENT_TYPE_TO_CA_ACTION[LessonElementType.ENERGIZER]

    def test_game_challenge_ca_action(self):
        elem = GameChallengeElement.model_validate(_game_challenge())
        assert elem.ca_action == ELEMENT_TYPE_TO_CA_ACTION[LessonElementType.GAME_CHALLENGE]

    def test_overrides_wrong_ca_action(self):
        elem = LectureElement.model_validate(_lecture(ca_action=999))
        assert elem.ca_action == ELEMENT_TYPE_TO_CA_ACTION[LessonElementType.LECTURE]


class TestToCaSchedule:
    def test_single_lecture(self):
        sections = [_section(1, 1, 10, _lecture())]
        agenda = LessonAgenda.model_validate(_agenda_data(sections))
        schedule = agenda.to_ca_schedule()
        assert schedule == [{"time": 1, "action": 1}]

    def test_group_activity_includes_duration(self):
        sections = [_section(1, 1, 15, _group_activity())]
        agenda = LessonAgenda.model_validate(_agenda_data(sections))
        schedule = agenda.to_ca_schedule()
        assert schedule == [{"time": 1, "action": 3, "duration": 15}]

    def test_game_challenge_includes_duration(self):
        sections = [_section(1, 1, 10, _game_challenge())]
        agenda = LessonAgenda.model_validate(_agenda_data(sections))
        schedule = agenda.to_ca_schedule()
        assert schedule == [{"time": 1, "action": 6, "duration": 10}]

    def test_sorted_by_time(self):
        sections = [
            _section(1, 11, 10, _energizer()),
            _section(2, 1, 10, _lecture()),
        ]
        agenda = LessonAgenda.model_validate(_agenda_data(sections))
        schedule = agenda.to_ca_schedule()
        assert schedule[0]["time"] < schedule[1]["time"]

    def test_mixed_sections(self):
        sections = [
            _section(1, 1, 10, _lecture()),
            _section(2, 11, 15, _group_activity()),
            _section(3, 26, 5, _energizer()),
        ]
        agenda = LessonAgenda.model_validate(_agenda_data(sections))
        schedule = agenda.to_ca_schedule()
        assert len(schedule) == 3
        assert schedule[0] == {"time": 1, "action": 1}
        assert schedule[1] == {"time": 11, "action": 3, "duration": 15}
        assert schedule[2] == {"time": 26, "action": 5}
