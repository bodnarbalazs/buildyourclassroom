from enum import Enum


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    SHORT_ANSWER = "short_answer"
    MATCHING = "matching"
    ESSAY = "essay"
