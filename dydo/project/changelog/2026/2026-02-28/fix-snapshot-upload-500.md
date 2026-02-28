---
area: general
type: changelog
date: 2026-02-28
---

# Task: fix-snapshot-upload-500

(No description)

## Progress

- [ ] (Not started)

## Files Changed

/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/workers/analyze_snapshot_worker.py — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Domain/Messages/AnalyzeSnapshotCommand.cs — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Domain/Messages/AnalyzeSnapshotResult.cs — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Domain/Messages/IAnalyzeSnapshotClient.cs — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Domain/Messages/FaceResultDto.cs — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Domain/Messages/BboxDto.cs — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Infrastructure/Services/Messaging/RabbitMqAnalyzeSnapshotClient.cs — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/tests/workers/test_analyze_snapshot_worker.py — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/api/models/agenda/generate_agenda_response.py — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/tests/test_agenda_models.py — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/tests/test_agenda_generator.py — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/tests/test_agenda_routes.py — Created
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/services/emotion_analyzer.py — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Domain/Messages/HackathonQueues.cs — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.AppHost/AppHost.cs — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Infrastructure/ServiceCollectionExtensions.cs — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/backend/Hackathon.Api/Endpoints/MicroserviceEndpoints.cs — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/api/models/agenda/lecture_element.py — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/api/models/agenda/targeted_check_element.py — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/api/models/agenda/group_activity_element.py — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/api/models/agenda/individual_support_element.py — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/api/models/agenda/energizer_element.py — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/api/models/agenda/game_challenge_element.py — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/api/routes/agenda.py — Modified
/Users/dezsenyigyorgy/sajat/GitHub/buildyourclassroom/src/microservices/microservice/services/agenda_generator.py — Modified


## Review Summary

Fixed 500 error on snapshot upload. DeepFace returns np.float32 values in emotion scores dict. These were passed directly to a JSONB column in PostgreSQL, and Python's json.dumps cannot serialize np.float32. Fixed by converting to native float at the data boundary in emotion_analyzer.py line 117: {k: float(v) for k, v in ...}. Verified with a live upload test — 200 OK.

## Code Review

- Reviewed by: Dylan
- Date: 2026-02-27 20:02
- Result: PASSED
- Notes: Both changes are correct. (1) emotion_analyzer.py:117 — float() conversion at the DeepFace data boundary fixes np.float32 JSON serialization for JSONB. Idiomatic, minimal, right location. (2) main.py import change from 'from shared.database import engine, init_db' to 'import shared.database as db' — necessary because engine is None at import time and only set by init_db(); the old named import would have captured the stale None reference. Tests pass (27/27).

Awaiting human approval.

## Approval

- Approved: 2026-02-28 01:09
