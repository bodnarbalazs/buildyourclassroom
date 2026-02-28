---
area: general
name: stt-env-var-simplify
status: human-reviewed
created: 2026-02-28T02:37:22.8327350Z
assigned: Carla
updated: 2026-02-28T02:38:24.7595680Z
---

# Task: stt-env-var-simplify

(No description)

## Progress

- [ ] (Not started)

## Files Changed

(None yet)

## Review Summary

Simplified Azure OpenAI env var setup: all three services (agenda, chat/assessment, whisper/transcription) now share AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY. Only deployment names differ — added AZURE_OPENAI_CHAT_DEPLOYMENT_NAME and AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME. Changed AppHost.cs, assessment_generator.py, and transcription_service.py.

## Code Review

- Reviewed by: Dylan
- Date: 2026-02-28 02:39
- Result: PASSED
- Notes: LGTM. Shared AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY across all three services, deployment names correctly differentiated. AppHost wiring is consistent with Python consumers. No security issues, no slop, no unnecessary complexity.

Awaiting human approval.