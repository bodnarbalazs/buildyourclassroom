from __future__ import annotations

import json
import os

import structlog
from openai import AsyncAzureOpenAI
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from api.models.agenda import LessonAgenda

logger = structlog.get_logger()

SYSTEM_PROMPT = """\
You are an expert instructional designer who understands classroom engagement dynamics \
and the science of learning. You design well-paced, pedagogically sound lesson agendas \
that keep students engaged through a variety of teaching techniques.

You must output valid JSON matching the schema below EXACTLY. No extra keys, no missing keys.

## Lesson Element Types

Every section of the agenda must use exactly one of these element types:

### LECTURE (ca_action: 1)
Standard instructor-led teaching. Periodically poses comprehension questions to re-engage \
drifting students.
Required fields: element_type, pedagogical_rationale, key_points (list of strings), \
instructor_notes (string).

### TARGETED_CHECK (ca_action: 2)
Focused check-in on a small group — instructor moves to a cluster of students to ask \
questions or review work.
Required fields: element_type, pedagogical_rationale, focus_area (string), \
questions (list of strings).

### GROUP_ACTIVITY (ca_action: 3)
Collaborative task where peer interaction drives engagement. Requires a duration.
Required fields: element_type, pedagogical_rationale, activity_title (string), \
instructions (string), group_size (int), materials_needed (list of strings).

### INDIVIDUAL_SUPPORT (ca_action: 4)
Instructor pauses whole-class flow to help a struggling student one-on-one. Brief, causes \
slight disengagement for the rest.
Required fields: element_type, pedagogical_rationale, support_focus (string), \
follow_up (string).

### ENERGIZER (ca_action: 5)
Short burst to re-energize: humor, anecdote, surprising fact, short video, or a brain break.
Required fields: element_type, pedagogical_rationale, \
energizer_type (one of: "humor", "anecdote", "fun_fact", "video_clip", "brain_break"), \
description (string).

### GAME_CHALLENGE (ca_action: 6)
Competitive or gamified activity that boosts energy and triggers sustained peer interaction. \
Requires a duration.
Required fields: element_type, pedagogical_rationale, game_title (string), \
rules (string), team_based (bool).

## Output JSON Schema

{
  "lesson_title": "string",
  "subject": "string",
  "target_audience": "string",
  "total_duration_minutes": <int>,
  "overall_objectives": ["string", ...],
  "sections": [
    {
      "order": <int, 1-based>,
      "title": "string",
      "description": "string",
      "start_minute": <int, 1-based>,
      "duration_minutes": <int>,
      "learning_objectives": ["string", ...],
      "element": {
        "element_type": "<one of the 6 types>",
        "pedagogical_rationale": "string",
        ... type-specific fields ...
      }
    }
  ],
  "summary": "string"
}

## IMPORTANT RULES

1. The user's additional instructions take ABSOLUTE PRIORITY over default recommendations. \
If the user requests specific element types (e.g. "only lectures", "no group activities"), \
you MUST follow those instructions exactly. When no specific preference is given, default to \
a balanced mix of element types for good engagement.
2. start_minute values must be sequential and non-overlapping: each section's start_minute \
equals the previous section's start_minute + duration_minutes. The first section starts at \
minute 1.
3. All sections' duration_minutes must sum to total_duration_minutes exactly.
4. Include pedagogical_rationale on each section explaining why that element type was chosen \
at that point in the lesson.
5. Do NOT include a ca_action field in the element — it will be derived automatically.
6. Output ONLY valid JSON. No markdown, no code fences, no commentary outside the JSON object.\
"""


def _build_user_prompt(
    subject: str,
    topic: str,
    target_audience: str,
    duration_minutes: int,
    additional_instructions: str | None,
) -> str:
    prompt = (
        f"Create a detailed lesson agenda for a {duration_minutes}-minute lesson.\n\n"
        f"Subject: {subject}\n"
        f"Topic: {topic}\n"
        f"Target audience: {target_audience}\n"
        f"Total duration: {duration_minutes} minutes\n"
    )
    if additional_instructions:
        prompt += (
            f"\n## USER INSTRUCTIONS (MUST FOLLOW)\n"
            f"{additional_instructions}\n"
        )
    return prompt


class AgendaGenerationError(Exception):
    pass


_REQUIRED_ENV_VARS = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT_NAME"]


class AgendaGenerator:
    def __init__(self) -> None:
        missing = [v for v in _REQUIRED_ENV_VARS if v not in os.environ]
        if missing:
            raise AgendaGenerationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        self._client = AsyncAzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
        self._deployment = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_llm(self, messages: list[dict]) -> str:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if content is None:
            raise AgendaGenerationError("LLM returned empty response")
        return content

    async def generate(
        self,
        subject: str,
        topic: str,
        target_audience: str,
        duration_minutes: int,
        additional_instructions: str | None = None,
    ) -> LessonAgenda:
        user_prompt = _build_user_prompt(
            subject, topic, target_audience, duration_minutes, additional_instructions
        )
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        raw = await self._call_llm(messages)
        log = logger.bind(subject=subject, topic=topic)

        try:
            data = json.loads(raw)
            return LessonAgenda.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as first_err:
            log.warning("first_parse_failed", error=str(first_err))

        # Retry with a fix-up message
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": (
                "Your previous response was not valid JSON matching the required schema. "
                f"Error: {first_err}. "
                "Please fix the JSON and return ONLY the corrected JSON object."
            ),
        })

        raw_retry = await self._call_llm(messages)
        try:
            data = json.loads(raw_retry)
            return LessonAgenda.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as second_err:
            log.error("second_parse_failed", error=str(second_err))
            raise AgendaGenerationError(
                f"LLM failed to produce valid agenda after retry: {second_err}"
            ) from second_err
