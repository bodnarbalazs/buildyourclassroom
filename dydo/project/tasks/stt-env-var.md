---
area: general
name: stt-env-var
status: human-reviewed
created: 2026-02-28T02:33:34.0202250Z
assigned: Carla
updated: 2026-02-28T02:36:15.8119920Z
---

# Task: stt-env-var

(No description)

## Progress

- [ ] (Not started)

## Files Changed

(None yet)

## Review Summary

Added Aspire parameters and WithEnvironment calls for AZURE_OPENAI_CHAT_* and AZURE_OPENAI_WHISPER_* env vars to AppHost.cs. These match the existing env var names expected by AssessmentGenerator and TranscriptionService in the Python microservice. No deviations from expected approach — purely wiring work.

## Code Review

- Reviewed by: Dylan
- Date: 2026-02-28 02:38
- Result: PASSED
- Notes: LGTM. All 6 env var names match exactly what assessment_generator.py and transcription_service.py expect. Secrets marked correctly. Build passes with 0 warnings. Clean, surgical wiring work.

Awaiting human approval.