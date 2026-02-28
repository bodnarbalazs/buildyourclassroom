---
area: general
name: lesson-assessment-generator
status: review-pending
created: 2026-02-28T00:32:26.7390150Z
assigned: Bella
updated: 2026-02-28T00:48:42.3542220Z
---

# Task: lesson-assessment-generator

(No description)

## Progress

- [ ] (Not started)

## Files Changed

(None yet)

## Review Summary

Implemented a two-stage lesson assessment generation pipeline: (1) TranscriptionService using Azure OpenAI Whisper with video audio extraction via pydub/ffmpeg, auto-chunking for files >25MB with silence-aware splitting and context carry-over, retry logic. (2) AssessmentGenerator using Azure OpenAI chat completions that produces a full AssessmentBundle (Quiz, PracticeTest, Exam) from transcript content only, with tiktoken-based token counting, summarization fallback for long transcripts, and retry with corrective prompt on validation failure. All Pydantic v2 models follow one-type-per-file convention with discriminated unions on question_type. Two API endpoints: multipart file upload and JSON transcript. 34 new tests, all 98 tests pass. Key decisions: used pydub for audio processing (needed audioop-lts for Python 3.13 compat), used synchronous Whisper client wrapped with asyncio.to_thread since the SDK is blocking, structured practice_test/exam questions as {base, topic_tag, bloom_level} wrapper to cleanly separate the discriminated union from the enrichment fields.

## Code Review

- Reviewed by: Carla
- Date: 2026-02-28 00:45
- Result: PASSED
- Notes: LGTM. Code is clean, tests pass. Well-structured two-stage pipeline following existing codebase patterns (matches agenda_generator structure). Models follow one-type-per-file convention with appropriate discriminated unions. 34 new tests covering models, routes, and error paths. All 104 tests pass with no regressions. One borderline note: MatchingPair lives in matching_question.py (technically violates one-type-per-file rule), but it's a 2-field value object tightly coupled to MatchingQuestion — splitting it would add noise without benefit.

Awaiting human approval.