---
area: microservices
type: changelog
date: 2026-02-27
---

# Replace engagement levels with learning-quality model

Engagement scoring now uses five pedagogically meaningful levels instead of generic high/medium/low. Each level maps to a signal group of DeepFace emotions and carries a learning-quality score.

## What Changed

- Engagement levels changed from `high/medium/low` to `engaged/passive/confused/anxious/disruptive`
- `compute_engagement()` rewritten to use signal-grouping: raw DeepFace emotions are summed into four signal groups, and the dominant group (>40% combined) determines the level
- Score now represents how conducive the detected state is to learning (1.0 = engaged, down to 0.1 = disruptive)
- `engagement_level` DB column widened from `String(10)` to `String(15)` to fit longer level names

## Signal Groups

| Level | Emotions | Quality Score |
|-------|----------|---------------|
| engaged | happy + surprise | 1.0 |
| passive | neutral | 0.5 |
| confused | (no dominant signal <40%) | 0.3 |
| anxious | sad + fear | 0.2 |
| disruptive | angry + disgust | 0.1 |

## Why

Generic high/medium/low levels didn't convey the pedagogical meaning of the detected state. A teacher seeing "low engagement" can't act on that. Seeing "confused" vs "anxious" vs "disruptive" tells them what kind of intervention is needed.

## Impact

- API responses now return new level names — any frontend consuming `engagement_level` must be updated
- Existing database rows with old level values will be inconsistent with new values (migration or backfill needed for existing data)

## Files Changed

| File | Change |
|------|--------|
| `src/microservices/microservice/services/emotion_analyzer.py` | Rewrote `compute_engagement()`, added `LEVEL_QUALITY` dict and `_DOMINANCE_THRESHOLD` |
| `src/microservices/microservice/api/models/emotion_orm.py` | Widened `engagement_level` column from `String(10)` to `String(15)` |
| `src/microservices/microservice/tests/test_emotion_analyzer.py` | Updated tests for new levels and scoring |
| `src/microservices/microservice/tests/test_emotion_routes.py` | Updated test expectations for new levels |

## Related

- [Facial emotion detection](./facial-emotion-detection.md) — Parent feature this change refines
