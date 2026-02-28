from __future__ import annotations

import json
import os
import time

import structlog
import tiktoken
from openai import AsyncAzureOpenAI
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from api.models.assessment import AssessmentBundle

logger = structlog.get_logger()

DEFAULT_TOKEN_THRESHOLD = 60_000

SYSTEM_PROMPT = """\
You are an expert educator and assessment designer with deep expertise in pedagogy, \
Bloom's taxonomy, and formative/summative assessment design.

## HARD CONSTRAINT

Every question, answer, option, explanation, and rubric criterion you generate MUST be \
derived EXCLUSIVELY from information explicitly present in the provided lesson transcript. \
You MUST NOT introduce outside knowledge, external facts, examples, or assumptions beyond \
what was discussed in the transcript. If the transcript covers limited material, produce \
fewer questions rather than padding with invented content.

## Your Task

Analyze the lesson transcript and generate an AssessmentBundle containing:
1. A brief transcript_summary (3–5 sentences capturing main topics and flow)
2. A Quiz (formative, 5–10 questions)
3. A Practice Test (self-study, 15–25 questions, sectioned by topic)
4. An Exam (summative, 25–40 questions, sectioned, with points and rubrics)

## Quiz Specification

- 5–10 questions total
- Question types: multiple_choice (4 options, 1 correct), true_false, fill_in_the_blank
- Mix question types — do not make all questions the same type
- Each question: question_type, question_text, options (if multiple_choice), \
correct_answer (str for mc/fill, bool for t/f), explanation, difficulty (easy/medium/hard)
- assessment_type: "quiz"

## Practice Test Specification

- 15–25 questions total, organized into sections by topic/theme
- Question types: multiple_choice, true_false, short_answer, fill_in_the_blank, matching
- Each section: section_title, questions list
- Each question is an object with:
  - base: the question object (with question_type discriminator)
  - topic_tag: which lesson topic it tests
  - bloom_level: remember, understand, apply, or analyze
- assessment_type: "practice_test"

## Exam Specification

- 25–40 questions total, organized into sections
- Question types: multiple_choice, true_false, short_answer, fill_in_the_blank, \
matching, essay
- Each question is an object with:
  - base: the question object (with question_type discriminator)
  - topic_tag, bloom_level, points (integer >= 1)
- Essay questions must include grading_rubric (list of evaluation criteria) in the base
- Include total_points (sum of all question points) and time_limit_minutes (recommended)
- Weight toward higher-order thinking (apply, analyze) and harder difficulty
- assessment_type: "exam"

## Matching Questions

For matching type questions, include a "pairs" field (list of {left, right} objects) \
and set correct_answer to a description of the correct pairings.

## Distribution Rules

- Distribute questions across topics proportionally to how much time/depth each topic \
received in the lesson
- Write explanation fields that reference specific points from the lesson \
(e.g., "As discussed when covering Newton's second law...")
- Vary difficulty levels within each assessment

## AssessmentMetadata (shared by quiz, practice_test, exam)

Each assessment includes: title (str), subject (str), generated_from (str — lesson \
title or filename), assessment_type (literal), total_questions (int), \
created_at (ISO 8601 datetime string)

## Output

Return a single JSON object with this exact structure:
{
  "transcript_summary": "...",
  "quiz": { ...Quiz with metadata and flat questions list... },
  "practice_test": { ...PracticeTest with metadata and sections... },
  "exam": { ...Exam with metadata, sections, total_points, time_limit_minutes... }
}

Output ONLY valid JSON. No markdown, no code fences, no commentary outside the JSON.\
"""


def _build_user_prompt(
    transcript: str,
    subject: str | None,
    target_audience: str | None,
    additional_instructions: str | None,
) -> str:
    parts = ["Generate assessments from the following lesson transcript.\n"]
    if subject:
        parts.append(f"Subject: {subject}")
    if target_audience:
        parts.append(f"Target audience: {target_audience}")
    if additional_instructions:
        parts.append(f"Additional instructions: {additional_instructions}")
    parts.append(f"\n--- TRANSCRIPT ---\n{transcript}\n--- END TRANSCRIPT ---")
    return "\n".join(parts)


SUMMARY_PROMPT = """\
You are a meticulous note-taker. Produce a detailed, structured summary of the following \
lesson transcript. Preserve all key facts, definitions, examples, arguments, and \
conclusions. Organize by topic. This summary will be used to generate assessments, so \
completeness is critical — do not omit any substantive point.

Output ONLY the summary text, no JSON, no markdown fences.\
"""


class AssessmentGenerationError(Exception):
    pass


_REQUIRED_ENV_VARS = [
    "AZURE_OPENAI_CHAT_ENDPOINT",
    "AZURE_OPENAI_CHAT_API_KEY",
    "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME",
]


class AssessmentGenerator:
    def __init__(self) -> None:
        missing = [v for v in _REQUIRED_ENV_VARS if v not in os.environ]
        if missing:
            raise AssessmentGenerationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        self._client = AsyncAzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_CHAT_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_CHAT_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_CHAT_API_VERSION", "2024-10-21"),
        )
        self._deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
        self._token_threshold = int(
            os.environ.get("ASSESSMENT_TOKEN_THRESHOLD", str(DEFAULT_TOKEN_THRESHOLD))
        )
        try:
            self._encoding = tiktoken.encoding_for_model(self._deployment)
        except KeyError:
            self._encoding = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self._encoding.encode(text))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call_llm(self, messages: list[dict], json_mode: bool = True) -> str:
        kwargs: dict = {
            "model": self._deployment,
            "messages": messages,
            "temperature": 0.7,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = await self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        if content is None:
            raise AssessmentGenerationError("LLM returned empty response")
        return content

    async def _summarize_transcript(self, transcript: str) -> str:
        messages: list[dict] = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": transcript},
        ]
        return await self._call_llm(messages, json_mode=False)

    async def generate(
        self,
        transcript: str,
        subject: str | None = None,
        target_audience: str | None = None,
        additional_instructions: str | None = None,
        generated_from: str = "lesson",
    ) -> AssessmentBundle:
        log = logger.bind(generated_from=generated_from)
        start = time.monotonic()

        token_count = self._count_tokens(transcript)
        log.info("assessment_generation_started", transcript_tokens=token_count)

        effective_transcript = transcript
        if token_count > self._token_threshold:
            log.warning(
                "transcript_exceeds_threshold",
                tokens=token_count,
                threshold=self._token_threshold,
            )
            effective_transcript = await self._summarize_transcript(transcript)
            log.info(
                "transcript_summarized",
                summary_tokens=self._count_tokens(effective_transcript),
            )

        user_prompt = _build_user_prompt(
            effective_transcript, subject, target_audience, additional_instructions
        )
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        raw = await self._call_llm(messages)

        try:
            data = json.loads(raw)
            bundle = AssessmentBundle.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as first_err:
            log.warning("first_parse_failed", error=str(first_err))

            # Retry with corrective prompt
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
                bundle = AssessmentBundle.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as second_err:
                log.error("second_parse_failed", error=str(second_err))
                raise AssessmentGenerationError(
                    f"LLM failed to produce valid assessments after retry: {second_err}"
                ) from second_err

        duration = time.monotonic() - start
        log.info("assessment_generation_completed", duration_s=round(duration, 2))
        return bundle
