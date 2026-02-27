from enum import Enum


class LessonElementType(str, Enum):
    LECTURE = "LECTURE"
    TARGETED_CHECK = "TARGETED_CHECK"
    GROUP_ACTIVITY = "GROUP_ACTIVITY"
    INDIVIDUAL_SUPPORT = "INDIVIDUAL_SUPPORT"
    ENERGIZER = "ENERGIZER"
    GAME_CHALLENGE = "GAME_CHALLENGE"


ELEMENT_TYPE_TO_CA_ACTION: dict[LessonElementType, int] = {
    LessonElementType.LECTURE: 1,
    LessonElementType.TARGETED_CHECK: 2,
    LessonElementType.GROUP_ACTIVITY: 3,
    LessonElementType.INDIVIDUAL_SUPPORT: 4,
    LessonElementType.ENERGIZER: 5,
    LessonElementType.GAME_CHALLENGE: 6,
}
