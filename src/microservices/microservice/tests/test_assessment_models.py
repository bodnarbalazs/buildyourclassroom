"""Tests for assessment Pydantic models."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from api.models.assessment import (
    AssessmentBundle,
    Exam,
    ExamQuestion,
    ExamSection,
    MatchingPair,
    MatchingQuestion,
    MultipleChoiceQuestion,
    PracticeTest,
    PracticeTestQuestion,
    PracticeTestSection,
    Quiz,
    TrueFalseQuestion,
)


def _mc_question(**overrides):
    defaults = {
        "question_type": "multiple_choice",
        "question_text": "What is 2+2?",
        "options": ["1", "2", "3", "4"],
        "correct_answer": "4",
        "explanation": "Basic arithmetic",
        "difficulty": "easy",
    }
    defaults.update(overrides)
    return defaults


def _tf_question(**overrides):
    defaults = {
        "question_type": "true_false",
        "question_text": "The sky is blue.",
        "correct_answer": True,
        "explanation": "Observable fact",
        "difficulty": "easy",
    }
    defaults.update(overrides)
    return defaults


def _fill_question(**overrides):
    defaults = {
        "question_type": "fill_in_the_blank",
        "question_text": "Water is made of hydrogen and ___.",
        "correct_answer": "oxygen",
        "explanation": "Chemical composition",
        "difficulty": "medium",
    }
    defaults.update(overrides)
    return defaults


_NOW = datetime.now(tz=timezone.utc).isoformat()


def _quiz_data(n_questions=5):
    questions = []
    for i in range(n_questions):
        if i % 3 == 0:
            questions.append(_mc_question(question_text=f"MC question {i}?"))
        elif i % 3 == 1:
            questions.append(_tf_question(question_text=f"TF statement {i}."))
        else:
            questions.append(_fill_question(question_text=f"Fill blank {i}."))
    return {
        "title": "Test Quiz",
        "subject": "Science",
        "generated_from": "lesson.mp3",
        "assessment_type": "quiz",
        "total_questions": n_questions,
        "created_at": _NOW,
        "questions": questions,
    }


class TestMultipleChoiceQuestion:
    def test_valid(self):
        q = MultipleChoiceQuestion.model_validate(_mc_question())
        assert q.question_type.value == "multiple_choice"
        assert len(q.options) == 4

    def test_requires_four_options(self):
        with pytest.raises(ValidationError):
            MultipleChoiceQuestion.model_validate(_mc_question(options=["a", "b"]))


class TestTrueFalseQuestion:
    def test_valid(self):
        q = TrueFalseQuestion.model_validate(_tf_question())
        assert q.correct_answer is True


class TestMatchingQuestion:
    def test_valid(self):
        data = {
            "question_type": "matching",
            "question_text": "Match terms",
            "pairs": [{"left": "H2O", "right": "Water"}, {"left": "NaCl", "right": "Salt"}],
            "correct_answer": "H2O->Water, NaCl->Salt",
            "explanation": "Chemistry",
            "difficulty": "medium",
        }
        q = MatchingQuestion.model_validate(data)
        assert len(q.pairs) == 2
        assert isinstance(q.pairs[0], MatchingPair)

    def test_requires_min_two_pairs(self):
        data = {
            "question_type": "matching",
            "question_text": "Match",
            "pairs": [{"left": "a", "right": "b"}],
            "correct_answer": "a->b",
            "explanation": "Test",
            "difficulty": "easy",
        }
        with pytest.raises(ValidationError):
            MatchingQuestion.model_validate(data)


class TestQuiz:
    def test_valid_quiz(self):
        quiz = Quiz.model_validate(_quiz_data(5))
        assert quiz.assessment_type == "quiz"
        assert quiz.total_questions == 5
        assert len(quiz.questions) == 5

    def test_quiz_too_few_questions(self):
        with pytest.raises(ValidationError):
            Quiz.model_validate(_quiz_data(3))

    def test_quiz_too_many_questions(self):
        with pytest.raises(ValidationError):
            Quiz.model_validate(_quiz_data(12))

    def test_discriminated_union_dispatch(self):
        quiz = Quiz.model_validate(_quiz_data(6))
        types = {type(q).__name__ for q in quiz.questions}
        assert "MultipleChoiceQuestion" in types
        assert "TrueFalseQuestion" in types


class TestPracticeTest:
    def test_valid(self):
        pt_data = {
            "title": "Practice",
            "subject": "Math",
            "generated_from": "lecture.wav",
            "assessment_type": "practice_test",
            "total_questions": 1,
            "created_at": _NOW,
            "sections": [
                {
                    "section_title": "Algebra",
                    "questions": [
                        {
                            "base": _mc_question(),
                            "topic_tag": "algebra",
                            "bloom_level": "understand",
                        }
                    ],
                }
            ],
        }
        pt = PracticeTest.model_validate(pt_data)
        assert len(pt.sections) == 1
        assert isinstance(pt.sections[0], PracticeTestSection)
        assert isinstance(pt.sections[0].questions[0], PracticeTestQuestion)


class TestExam:
    def test_valid(self):
        exam_data = {
            "title": "Final Exam",
            "subject": "Physics",
            "generated_from": "recording.mp4",
            "assessment_type": "exam",
            "total_questions": 1,
            "created_at": _NOW,
            "total_points": 10,
            "time_limit_minutes": 60,
            "sections": [
                {
                    "section_title": "Mechanics",
                    "questions": [
                        {
                            "base": _mc_question(),
                            "topic_tag": "mechanics",
                            "bloom_level": "apply",
                            "points": 10,
                        }
                    ],
                }
            ],
        }
        exam = Exam.model_validate(exam_data)
        assert exam.total_points == 10
        assert isinstance(exam.sections[0].questions[0], ExamQuestion)

    def test_essay_question_in_exam(self):
        essay_q = {
            "question_type": "essay",
            "question_text": "Explain Newton's laws.",
            "correct_answer": "Newton's three laws describe...",
            "explanation": "Covered in lesson",
            "difficulty": "hard",
            "grading_rubric": ["Accuracy", "Completeness", "Clarity"],
        }
        exam_data = {
            "title": "Exam",
            "subject": "Physics",
            "generated_from": "lesson.mp3",
            "assessment_type": "exam",
            "total_questions": 1,
            "created_at": _NOW,
            "total_points": 20,
            "time_limit_minutes": 90,
            "sections": [
                {
                    "section_title": "Essays",
                    "questions": [
                        {
                            "base": essay_q,
                            "topic_tag": "newton",
                            "bloom_level": "analyze",
                            "points": 20,
                        }
                    ],
                }
            ],
        }
        exam = Exam.model_validate(exam_data)
        assert exam.sections[0].questions[0].base.grading_rubric == [
            "Accuracy",
            "Completeness",
            "Clarity",
        ]


class TestAssessmentBundle:
    def test_valid(self):
        bundle_data = {
            "transcript_summary": "A lesson about basic math.",
            "quiz": _quiz_data(5),
            "practice_test": {
                "title": "Practice",
                "subject": "Math",
                "generated_from": "lesson.mp3",
                "assessment_type": "practice_test",
                "total_questions": 1,
                "created_at": _NOW,
                "sections": [
                    {
                        "section_title": "Numbers",
                        "questions": [
                            {
                                "base": _mc_question(),
                                "topic_tag": "numbers",
                                "bloom_level": "remember",
                            }
                        ],
                    }
                ],
            },
            "exam": {
                "title": "Exam",
                "subject": "Math",
                "generated_from": "lesson.mp3",
                "assessment_type": "exam",
                "total_questions": 1,
                "created_at": _NOW,
                "total_points": 5,
                "time_limit_minutes": 30,
                "sections": [
                    {
                        "section_title": "Math",
                        "questions": [
                            {
                                "base": _tf_question(),
                                "topic_tag": "math",
                                "bloom_level": "understand",
                                "points": 5,
                            }
                        ],
                    }
                ],
            },
        }
        bundle = AssessmentBundle.model_validate(bundle_data)
        assert bundle.transcript_summary == "A lesson about basic math."
        assert bundle.quiz.assessment_type == "quiz"
        assert bundle.practice_test.assessment_type == "practice_test"
        assert bundle.exam.assessment_type == "exam"
