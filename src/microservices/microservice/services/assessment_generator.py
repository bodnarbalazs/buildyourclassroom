from __future__ import annotations

import json
import os
import time

import structlog
import tiktoken
from openai import AsyncAzureOpenAI
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from api.models.assessment import AssessmentResult
from api.models.assessment.difficulty import Difficulty
from api.models.assessment.language import Language
from api.models.assessment.question_type import QuestionType
from api.models.assessment.test_type import TestType

logger = structlog.get_logger()

DEFAULT_TOKEN_THRESHOLD = 60_000

# Maps test_type to the output model structure the LLM should produce
_TEST_TYPE_MODEL = {
    TestType.QUICK_QUIZ: "quiz",
    TestType.CHAPTER_TEST: "practice_test",
    TestType.MIDTERM: "exam",
    TestType.FINAL_EXAM: "exam",
}

_QUESTION_TYPE_SPECS = {
    QuestionType.MULTIPLE_CHOICE: (
        "- multiple-choice: options (list of exactly 4 strings), "
        "correct_answer (string matching one option)"
    ),
    QuestionType.TRUE_FALSE: "- true-false: correct_answer (boolean)",
    QuestionType.SHORT_ANSWER: "- short-answer: correct_answer (string)",
    QuestionType.ESSAY: (
        "- essay: correct_answer (model answer string), "
        "grading_rubric (list of evaluation criteria strings, min 1)"
    ),
}


def _build_system_prompt(
    test_type: TestType,
    difficulty: Difficulty,
    num_questions: int,
    question_types: list[QuestionType],
    language: Language,
) -> str:
    qt_list = ", ".join(qt.value for qt in question_types)
    model = _TEST_TYPE_MODEL[test_type]

    parts = [
        "You are an expert educator and assessment designer with deep expertise in pedagogy, "
        "Bloom's taxonomy, and formative/summative assessment design.\n\n"
        "## HARD CONSTRAINT\n\n"
        "Every question, answer, option, explanation, and rubric criterion you generate MUST be "
        "derived EXCLUSIVELY from information explicitly present in the provided lesson transcript. "
        "You MUST NOT introduce outside knowledge, external facts, examples, or assumptions beyond "
        "what was discussed in the transcript. If the transcript covers limited material, produce "
        "fewer questions rather than padding with invented content.\n\n"
        "## Your Task\n\n"
        f"Generate a single {test_type.value} assessment from the lesson transcript.\n\n"
        "## Parameters\n\n"
        f"- Assessment type: {test_type.value}\n"
        f"- Difficulty: {difficulty.value}\n"
        f"- Number of questions: {num_questions}\n"
        f"- Allowed question types: {qt_list}\n"
        f"- Language: {language.value} (all content MUST be in this language)\n\n"
        "## Question Type Specifications\n\n"
        "Every question includes: question_type, question_text, explanation, difficulty.\n\n",
    ]

    for qt in question_types:
        parts.append(_QUESTION_TYPE_SPECS[qt] + "\n")

    parts.append("\n## Output Structure\n\n")

    if model == "quiz":
        parts.append(
            "The assessment object has metadata fields "
            "(title, subject, generated_from, assessment_type, total_questions, created_at) "
            'and a flat "questions" list of question objects.\n\n'
            f'assessment_type must be "{test_type.value}".\n'
        )
    elif model == "practice_test":
        parts.append(
            "The assessment object has metadata fields "
            "(title, subject, generated_from, assessment_type, total_questions, created_at) "
            'and "sections" (list of section objects).\n'
            "Each section: section_title (string), questions (list of question wrappers).\n"
            "Each wrapper: base (the question object), topic_tag (string), "
            'bloom_level ("remember", "understand", "apply", or "analyze").\n\n'
            f'assessment_type must be "{test_type.value}".\n'
        )
    else:
        parts.append(
            "The assessment object has metadata fields "
            "(title, subject, generated_from, assessment_type, total_questions, created_at), "
            '"sections" (list of section objects), '
            '"total_points" (integer, sum of all points), '
            '"time_limit_minutes" (integer).\n'
            "Each section: section_title (string), questions (list of question wrappers).\n"
            "Each wrapper: base (the question object), topic_tag (string), "
            'bloom_level ("remember", "understand", "apply", or "analyze"), '
            "points (integer >= 1).\n\n"
            f'assessment_type must be "{test_type.value}".\n'
        )

    parts.append(
        "\n## Distribution Rules\n\n"
        "- Distribute questions across topics proportionally to transcript coverage\n"
        "- Write explanations that reference specific transcript content\n"
        "- Mix question types from the allowed list\n\n"
        "## Output Format\n\n"
        'Return a single JSON object: {"transcript_summary": "...", "assessment": {...}}.\n'
        "Output ONLY valid JSON. No markdown, no code fences, no commentary."
    )

    return "".join(parts)


def _build_user_prompt(
    transcript: str,
    subject: str | None,
    target_audience: str | None,
    additional_instructions: str | None,
    generated_from: str,
) -> str:
    parts = ["Generate an assessment from the following lesson transcript.\n"]
    parts.append(f"Source: {generated_from}")
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
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
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
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
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
        test_type: TestType = TestType.CHAPTER_TEST,
        difficulty: Difficulty = Difficulty.MEDIUM,
        num_questions: int = 10,
        question_types: list[QuestionType] | None = None,
        language: Language = Language.ENGLISH,
        subject: str | None = None,
        target_audience: str | None = None,
        additional_instructions: str | None = None,
        generated_from: str = "lesson",
    ) -> AssessmentResult:
        if question_types is None:
            question_types = [QuestionType.MULTIPLE_CHOICE]

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

        system_prompt = _build_system_prompt(
            test_type, difficulty, num_questions, question_types, language
        )
        user_prompt = _build_user_prompt(
            effective_transcript, subject, target_audience,
            additional_instructions, generated_from,
        )
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        raw = await self._call_llm(messages)

        try:
            data = json.loads(raw)
            result = AssessmentResult.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as first_err:
            log.warning("first_parse_failed", error=str(first_err))

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
                result = AssessmentResult.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as second_err:
                log.error("second_parse_failed", error=str(second_err))
                raise AssessmentGenerationError(
                    f"LLM failed to produce valid assessment after retry: {second_err}"
                ) from second_err

        duration = time.monotonic() - start
        log.info("assessment_generation_completed", duration_s=round(duration, 2))
        return result
