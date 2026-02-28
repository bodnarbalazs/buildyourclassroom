---
area: microservices
type: reference
---

# Assessment API Reference

REST API for generating lesson assessments from audio, video, or text transcripts. Part of the Python FastAPI microservice.

---

## Endpoints

### POST /api/v1/generate-assessments

Upload an audio, video, or text file to generate a complete assessment bundle.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | yes | Audio (.mp3, .mpga, .m4a, .wav), video (.mp4, .webm, .mpeg), or text (.txt). Max 500 MB. |
| `subject` | string | no | Subject name (e.g., "Physics") |
| `target_audience` | string | no | Target audience (e.g., "Grade 10") |
| `additional_instructions` | string | no | Extra instructions for the generator |

**Response:** `200` — AssessmentBundle (see Response Models below)

**Errors:**

| Status | Cause |
|--------|-------|
| 400 | Unsupported file format, empty file, empty transcription result, or transcription error |
| 413 | File exceeds 500 MB |
| 502 | Azure OpenAI service error (Whisper or Chat) |

---

### POST /api/v1/generate-assessments/from-transcript

Submit a transcript directly as JSON.

**Content-Type:** `application/json`

```json
{
  "transcript": "Full lesson transcript text...",
  "subject": "Physics",
  "target_audience": "Grade 10",
  "additional_instructions": "Focus on thermodynamics"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | string | yes | Lesson transcript text (must not be empty) |
| `subject` | string | no | Subject name |
| `target_audience` | string | no | Target audience |
| `additional_instructions` | string | no | Extra instructions |

**Response:** `200` — AssessmentBundle (see Response Models below)

**Errors:**

| Status | Cause |
|--------|-------|
| 400 | Empty or whitespace-only transcript |
| 422 | Missing transcript field |
| 502 | Azure OpenAI service error |

---

## Response Models

### AssessmentBundle

Top-level response containing all three assessment types.

| Field | Type | Description |
|-------|------|-------------|
| `transcript_summary` | string | 3-5 sentence summary of the lesson |
| `quiz` | Quiz | Formative assessment (5-10 questions) |
| `practice_test` | PracticeTest | Self-study assessment organized by topic |
| `exam` | Exam | Summative assessment with points and time limit |

### Quiz

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Assessment title |
| `subject` | string | Subject name |
| `generated_from` | string | Source filename or "lesson" |
| `assessment_type` | `"quiz"` | Fixed literal |
| `total_questions` | int | Question count |
| `created_at` | datetime | ISO 8601 timestamp |
| `questions` | QuizQuestion[] | 5-10 questions: multiple choice, true/false, or fill-in-the-blank |

### PracticeTest

| Field | Type | Description |
|-------|------|-------------|
| `title`, `subject`, `generated_from`, `assessment_type` (`"practice_test"`), `total_questions`, `created_at` | — | Same as Quiz |
| `sections` | PracticeTestSection[] | Topic-organized sections (min 1) |

**PracticeTestSection:** `section_title` + `questions` (list of PracticeTestQuestion)

**PracticeTestQuestion:** `base` (question union) + `topic_tag` (string) + `bloom_level` (BloomLevel)

### Exam

| Field | Type | Description |
|-------|------|-------------|
| `title`, `subject`, `generated_from`, `assessment_type` (`"exam"`), `total_questions`, `created_at` | — | Same as Quiz |
| `sections` | ExamSection[] | Sections (min 1) |
| `total_points` | int | Total available points |
| `time_limit_minutes` | int | Time limit in minutes |

**ExamSection:** `section_title` + `questions` (list of ExamQuestion)

**ExamQuestion:** `base` (question union, includes essay) + `topic_tag` + `bloom_level` + `points` (int)

### Question Types

All questions include `question_text`, `correct_answer`, `explanation`, and `difficulty` (easy/medium/hard). Type-specific fields:

| Type | Discriminator | Extra Fields |
|------|--------------|--------------|
| `multiple_choice` | `question_type` | `options` (exactly 4 strings) |
| `true_false` | `question_type` | `correct_answer` is bool |
| `fill_in_the_blank` | `question_type` | — |
| `short_answer` | `question_type` | — |
| `matching` | `question_type` | `pairs` (list of {left, right}, min 2) |
| `essay` | `question_type` | `grading_rubric` (list of strings, min 1) |

**Quiz** uses: multiple choice, true/false, fill-in-the-blank

**Practice test** uses: multiple choice, true/false, short answer, fill-in-the-blank, matching

**Exam** uses: all six types including essay

### BloomLevel

Bloom's taxonomy cognitive levels used in practice test and exam questions:

`remember` | `understand` | `apply` | `analyze`

---

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_WHISPER_ENDPOINT` | Azure OpenAI endpoint for Whisper |
| `AZURE_OPENAI_WHISPER_API_KEY` | API key for Whisper |
| `AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME` | Whisper deployment name |
| `AZURE_OPENAI_CHAT_ENDPOINT` | Azure OpenAI endpoint for Chat |
| `AZURE_OPENAI_CHAT_API_KEY` | API key for Chat |
| `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` | Chat deployment name |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_WHISPER_API_VERSION` | `2024-10-21` | Whisper API version |
| `AZURE_OPENAI_CHAT_API_VERSION` | `2024-10-21` | Chat API version |
| `ASSESSMENT_TOKEN_THRESHOLD` | `60000` | Token count above which transcripts are summarized before generation |

### System Requirements

- **ffmpeg** must be on system PATH (used by pydub for audio/video processing)

---

## Related

- [Assessment Generator Changelog](../project/changelog/2026/2026-02-28/lesson-assessment-generator.md) — Implementation details and files changed
- [Architecture Overview](../understand/architecture.md) — System-level context
