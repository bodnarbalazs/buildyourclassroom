"""Tests for services/agenda_generator.py."""
from services.agenda_generator import _build_user_prompt


class TestBuildUserPrompt:
    def test_basic_prompt(self):
        result = _build_user_prompt("Math", "Algebra", "Grade 8", 45, None)
        assert "45-minute" in result
        assert "Math" in result
        assert "Algebra" in result
        assert "Grade 8" in result
        assert "Additional instructions" not in result

    def test_with_additional_instructions(self):
        result = _build_user_prompt("Science", "Physics", "Grade 10", 60, "Focus on labs")
        assert "Focus on labs" in result
        assert "Additional instructions" in result

    def test_empty_additional_instructions_ignored(self):
        result = _build_user_prompt("Art", "Painting", "Grade 3", 30, "")
        assert "Additional instructions" not in result
