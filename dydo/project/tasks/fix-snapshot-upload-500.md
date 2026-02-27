---
area: general
name: fix-snapshot-upload-500
status: human-reviewed
created: 2026-02-27T19:59:22.7229740Z
assigned: Carla
updated: 2026-02-27T20:01:00.9566600Z
---

# Task: fix-snapshot-upload-500

(No description)

## Progress

- [ ] (Not started)

## Files Changed

(None yet)

## Review Summary

Fixed 500 error on snapshot upload. DeepFace returns np.float32 values in emotion scores dict. These were passed directly to a JSONB column in PostgreSQL, and Python's json.dumps cannot serialize np.float32. Fixed by converting to native float at the data boundary in emotion_analyzer.py line 117: {k: float(v) for k, v in ...}. Verified with a live upload test — 200 OK.

## Code Review

- Reviewed by: Dylan
- Date: 2026-02-27 20:02
- Result: PASSED
- Notes: Both changes are correct. (1) emotion_analyzer.py:117 — float() conversion at the DeepFace data boundary fixes np.float32 JSON serialization for JSONB. Idiomatic, minimal, right location. (2) main.py import change from 'from shared.database import engine, init_db' to 'import shared.database as db' — necessary because engine is None at import time and only set by init_db(); the old named import would have captured the stale None reference. Tests pass (27/27).

Awaiting human approval.