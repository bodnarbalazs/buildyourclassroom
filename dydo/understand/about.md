---
area: understand
type: context
must-read: true
---

# About This Project

We're on a hackathon — we need to move fast. We only care about the future in principle, not really. So we shouldn't care about vendor lock-in or having databases not in containers.

**"We help Teach Teachers Teach"** — an AI-powered teaching toolkit with three tools:

### Classroom Builder

Teachers paste a lesson plan and an AI (Azure OpenAI) structures it into timed pedagogical segments — lectures, group activities, targeted checks, energizers, and more. A simulation then visualizes 30 students with real-time emotional states (engaged, passive, anxious, confused, disruptive), letting educators preview how a class might respond before they teach.

### Test Generator

Upload a recording or text of a lesson. The system transcribes it (via Whisper), then generates complete assessment bundles — quizzes, practice tests, and exams — with multiple question types, configurable difficulty, language selection, and Bloom's taxonomy alignment.

### Class Evaluation

A camera feed with DeepFace-based emotion detection tracks real-time attention and engagement per student. Sessions store timestamped snapshots, and the platform generates summary statistics and timeline analytics for reviewing how engagement shifted throughout a class.

---

*See [architecture.md](./architecture.md) for technical structure.*
