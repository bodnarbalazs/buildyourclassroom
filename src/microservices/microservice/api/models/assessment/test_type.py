from enum import Enum


class TestType(str, Enum):
    QUICK_QUIZ = "quick-quiz"
    CHAPTER_TEST = "chapter-test"
    MIDTERM = "midterm"
    FINAL_EXAM = "final-exam"
