"""Tests for services/assessment_generator.py."""
from services.assessment_generator import _build_user_prompt


class TestBuildUserPrompt:
    def test_basic_prompt_with_transcript(self):
        result = _build_user_prompt("Lesson about gravity.", None, None, None)
        assert "Lesson about gravity." in result
        assert "--- TRANSCRIPT ---" in result
        assert "--- END TRANSCRIPT ---" in result

    def test_includes_subject(self):
        result = _build_user_prompt("text", "Physics", None, None)
        assert "Subject: Physics" in result

    def test_includes_target_audience(self):
        result = _build_user_prompt("text", None, "Grade 10", None)
        assert "Target audience: Grade 10" in result

    def test_includes_additional_instructions(self):
        result = _build_user_prompt("text", None, None, "Focus on definitions")
        assert "Additional instructions: Focus on definitions" in result

    def test_all_fields(self):
        result = _build_user_prompt("transcript", "Math", "College", "Be strict")
        assert "Subject: Math" in result
        assert "Target audience: College" in result
        assert "Additional instructions: Be strict" in result
        assert "transcript" in result

    def test_none_fields_excluded(self):
        result = _build_user_prompt("text", None, None, None)
        assert "Subject:" not in result
        assert "Target audience:" not in result
        assert "Additional instructions:" not in result
