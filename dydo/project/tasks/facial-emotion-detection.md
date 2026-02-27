---
area: microservices
name: facial-emotion-detection
status: review-pending
created: 2026-02-27T18:56:37.4635790Z
assigned: Bella
---

# Task: facial-emotion-detection

Add real-time student engagement measurement to the Python microservice via facial emotion analysis. Webcam snapshots are uploaded via REST, analyzed with DeepFace, and results stored in PostgreSQL for aggregation and timeline views.

## Progress

- [x] Update pyproject.toml with dependencies (deepface, sqlalchemy[asyncio], asyncpg, opencv-python-headless, Pillow)
- [x] Create shared/database.py — async engine init, Npgsql→asyncpg connection string parser, FastAPI `get_db` dependency
- [x] Create api/models/emotion_orm.py — SQLAlchemy ORM: Session, Snapshot, FaceResult in `emotion` schema
- [x] Create api/models/emotion_schemas.py — Pydantic request/response models
- [x] Create services/emotion_analyzer.py — DeepFace wrapper, engagement scoring (weighted emotion→0.0–1.0)
- [x] Create services/emotion_repository.py — Async CRUD for sessions, snapshots, face results
- [x] Create api/routes/emotion.py — 7 REST endpoints under `/emotion/*`
- [x] Modify api/main.py — Lifespan handler for DB init, schema/table creation, model warm-up; include emotion router
- [x] Modify AppHost.cs — Wire PostgreSQL reference and WaitFor to microservice
- [x] Create tests (test_database.py, test_emotion_analyzer.py, test_emotion_routes.py)

## Files Changed

### New Files

| File | Purpose |
|------|---------|
| `src/microservices/microservice/shared/database.py` | Async DB engine, Npgsql parser, `get_db` dependency |
| `src/microservices/microservice/api/models/emotion_orm.py` | ORM models: Session, Snapshot, FaceResult |
| `src/microservices/microservice/api/models/emotion_schemas.py` | Pydantic request/response schemas |
| `src/microservices/microservice/api/routes/emotion.py` | `/emotion/*` REST endpoints |
| `src/microservices/microservice/services/emotion_analyzer.py` | DeepFace wrapper + engagement scoring |
| `src/microservices/microservice/services/emotion_repository.py` | Async repository for emotion data |
| `src/microservices/microservice/tests/test_database.py` | Connection string parser tests |
| `src/microservices/microservice/tests/test_emotion_analyzer.py` | Analyzer + engagement scoring tests |
| `src/microservices/microservice/tests/test_emotion_routes.py` | API endpoint integration tests |

### Modified Files

| File | Change |
|------|--------|
| `src/microservices/microservice/pyproject.toml` | Added deepface, opencv-python-headless, sqlalchemy[asyncio], asyncpg, numpy, Pillow |
| `src/microservices/microservice/api/main.py` | Added lifespan handler (DB init, table creation, model warm-up), included emotion router |
| `src/backend/Hackathon.AppHost/AppHost.cs` | Added `.WithReference(hackathonDb).WaitFor(postgres)` to microservice resource |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/emotion/sessions` | Start a monitoring session |
| `GET` | `/emotion/sessions` | List sessions (paginated) |
| `GET` | `/emotion/sessions/{id}` | Session details |
| `PATCH` | `/emotion/sessions/{id}/end` | End a session |
| `POST` | `/emotion/sessions/{id}/snapshots` | Upload snapshot → emotion analysis |
| `GET` | `/emotion/sessions/{id}/summary` | Aggregated engagement summary |
| `GET` | `/emotion/sessions/{id}/timeline` | Engagement over time (bucketed) |

## Key Design Decisions

- **DeepFace** with OpenCV backend for face detection + emotion classification
- Separate `emotion` DB schema to avoid conflicts with .NET EF Core `public` schema
- Engagement scoring: signal-grouped emotions → 5 learning-quality levels. Groups: happy+surprise→engaged (1.0), neutral→passive (0.5), sad+fear→anxious (0.2), angry+disgust→disruptive (0.1). No dominant signal (<40%)→confused (0.3). Score = quality × signal strength.
- Async throughout: SQLAlchemy async + asyncpg + FastAPI async endpoints
- Model warm-up at startup via lifespan handler to avoid cold-start latency

## Review Summary

(Pending)