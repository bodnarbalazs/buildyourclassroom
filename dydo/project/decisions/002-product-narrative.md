---
type: decision
status: accepted
date: 2026-02-28
area: product
---

# 002 — Product Narrative: Closing the Feedback Loop

The three tools are not separate products. They form one closed-loop system for teaching: predict, observe, measure.

## Context

The platform has three tools — Classroom Builder, Class Evaluation, Test Generator — that risk looking like three unrelated AI demos bolted onto one landing page. We needed a coherent story for the hackathon pitch.

## Decision

### The problem we're solving

Teaching is one of the only professions with almost zero real-time feedback. A surgeon sees vitals. A pilot has instruments. A teacher stands in front of 30 faces and guesses.

### The pitch

> "We close the feedback loop for teaching."

### The three tools map to one cycle

| Phase | Tool | Question it answers |
|-------|------|---------------------|
| **Before class** | Classroom Builder | "Will this lesson work?" |
| **During class** | Class Evaluation | "Is it working right now?" |
| **After class** | Test Generator | "Did it actually work?" |

This is **predict → observe → measure**. One loop, not three products.

### How to present it

Lead with the problem (teachers are flying blind), not the technology. Frame the demo as walking through one lesson's lifecycle:

1. **Plan it** — paste a lesson plan, AI structures it into timed segments
2. **Preview it** — simulation shows predicted student engagement
3. **Teach it** — live camera feed tracks real engagement
4. **Assess it** — upload the recording, get targeted assessments

The tools don't need to be technically connected for the demo. The narrative connection is sufficient: same lesson, three stages, one teacher dashboard.

### Future potential (mention, don't build)

If asked "what's next?", these are the natural extensions:

- **Simulation calibration** — real engagement data from Class Evaluation feeds back to improve Classroom Builder predictions
- **Engagement-aware assessment** — Test Generator weights questions toward segments where engagement was low
- **Unified lesson entity** — all three tools reference the same lesson, data flows between them automatically

These are vision items, not hackathon scope.

## Alternatives Considered

- **"AI toolkit for teachers"** — Too generic, sounds like a feature list.
- **Leading with technology** — "We use DeepFace + Whisper + GPT" impresses engineers, not judges.
- **Separate product pitches** — Dilutes impact, raises "why is this one platform?" questions.

## Consequences

- All agents working on any tool should understand it as part of this cycle
- The landing page / home screen should reflect predict → observe → measure
- Demo order should follow the teaching lifecycle, not the order features were built
