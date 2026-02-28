---
area: microservices
type: changelog
date: 2026-02-28
---

# Add lesson assessment generation service

Two-stage pipeline that transforms lesson recordings or transcripts into complete assessment bundles (quiz, practice test, exam). Stage 1 transcribes audio/video via Azure OpenAI Whisper with intelligent chunking; Stage 2 generates structured assessments via Azure OpenAI Chat with Bloom's taxonomy alignment.

## What Changed

- 2 new REST endpoints under `/api/v1/`: multipart file upload (`/generate-assessments`) and JSON transcript input (`/generate-assessments/from-transcript`)
- TranscriptionService: Azure Whisper integration with video-to-audio extraction (pydub/ffmpeg), silence-aware chunking for files >24 MB, context carry-over between chunks, retry logic
- AssessmentGenerator: Azure OpenAI Chat integration with tiktoken-based token counting, automatic summarization for long transcripts (>60k tokens), JSON validation with corrective retry on schema failure
- Full Pydantic v2 model hierarchy: 6 question types (multiple choice, true/false, fill-in-the-blank, short answer, matching, essay) combined into Quiz, PracticeTest, and Exam via discriminated unions, wrapped in AssessmentBundle
- 35 new tests covering models, routes, and generation logic (all 107 tests pass)

## Why

Teachers need a way to generate assessments from their lesson content. By accepting recordings or transcripts and producing structured quizzes, practice tests, and exams, the platform closes the loop between teaching and evaluation.

## Impact

- New dependencies: pydub (audio processing), tiktoken (token counting), audioop-lts (Python 3.13 compatibility for pydub)
- Requires ffmpeg on system PATH for video/audio processing
- 6 new environment variables for Azure OpenAI Whisper and Chat endpoints
- System prompt enforces transcript-only content generation (no external knowledge)

## Files Changed

### New

- `src/microservices/microservice/api/models/assessment/` (15 model files: question types, enums, quiz, practice test, exam, bundle, request)
- `src/microservices/microservice/api/routes/assessment.py`
- `src/microservices/microservice/services/assessment_generator.py`
- `src/microservices/microservice/services/transcription_service.py`
- `src/microservices/microservice/tests/test_assessment_generator.py`
- `src/microservices/microservice/tests/test_assessment_models.py`
- `src/microservices/microservice/tests/test_assessment_routes.py`

### Modified

- `src/microservices/microservice/api/main.py` (route registration)
- `src/microservices/microservice/pyproject.toml` (new dependencies)
- `src/microservices/microservice/uv.lock`

## Related

- [Assessment API Reference](../../../../reference/assessment-api.md) — Endpoint specifications and models
- [Architecture Overview](../../../../understand/architecture.md) — System-level context
