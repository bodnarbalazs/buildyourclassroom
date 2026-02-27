---
area: microservices
type: changelog
date: 2026-02-27
---

# Add facial emotion detection to Python microservice

Real-time student engagement measurement via webcam snapshot analysis. Images uploaded to `/emotion/sessions/{id}/snapshots` are processed by DeepFace for per-face emotion classification, then scored for engagement and stored in PostgreSQL for summary and timeline queries.

## What Changed

- 7 new REST endpoints under `/emotion/*` (session CRUD, snapshot upload, summary, timeline)
- DeepFace integration with OpenCV backend for face detection + emotion classification
- Engagement scoring: signal-grouped emotion mapping to 0.0–1.0 scale (engaged/passive/confused/anxious/disruptive)
- Async database layer: SQLAlchemy async + asyncpg in a separate `emotion` schema
- Aspire wiring: microservice now receives PostgreSQL connection string and waits for postgres

## Why

The project needs to measure student engagement during lessons. Facial emotion analysis from periodic webcam snapshots provides a non-intrusive, automated signal.

## Impact

- New dependency footprint: deepface, tensorflow-keras, opencv-python-headless, sqlalchemy[asyncio], asyncpg
- New `emotion` PostgreSQL schema with 3 tables (sessions, snapshots, face_results)
- First DeepFace model download triggered on startup (warm-up in lifespan handler)

## Files Changed

### New

- `src/microservices/microservice/shared/database.py`
- `src/microservices/microservice/api/models/emotion_orm.py`
- `src/microservices/microservice/api/models/emotion_schemas.py`
- `src/microservices/microservice/api/routes/emotion.py`
- `src/microservices/microservice/services/emotion_analyzer.py`
- `src/microservices/microservice/services/emotion_repository.py`
- `src/microservices/microservice/tests/test_database.py`
- `src/microservices/microservice/tests/test_emotion_analyzer.py`
- `src/microservices/microservice/tests/test_emotion_routes.py`

### Modified

- `src/microservices/microservice/pyproject.toml`
- `src/microservices/microservice/api/main.py`
- `src/backend/Hackathon.AppHost/AppHost.cs`
