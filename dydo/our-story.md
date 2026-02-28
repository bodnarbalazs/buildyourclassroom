# Our Story

## Inspiration

We were eager to come here to build as much as we can and challenge ourselves.

Initially, before the exact challenge descriptions came out, we eyed the healthcare one — we wanted to build a 3D tumor simulation model with Three.js: vascular system, angiogenesis, necrotic spread, immune response, and probably some other variables which would have overcomplicated that submission too.

We chose the education challenge because it felt a bit more open, and we did manage to do a cellular automaton model — but in our version the cells are students, and instead of simulating molecular signals spreading, we diffuse the spread of attention and the lack of it. We're grateful for the mentoring opportunities we've had; they gave us a lot of great ideas, including the live camera feed attention detection.

## What It Does

Our solution has three parts, all tied into a single thread: **helping teachers improve their teaching capabilities** — before, during, and after class.

**Classroom Builder** — Teachers simulate their lesson plan's effects on a virtual classroom (random or configured to match their own). An AI structures the plan into timed pedagogical segments, then a cellular automaton visualizes 30 students with real-time emotional states — showing how attention spreads and how they should pace interactions.

- AI-powered lesson plan structuring (Azure OpenAI)
- Timed segments: lectures, group activities, targeted checks, energizers
- Real-time student simulation with emotional states (engaged, passive, anxious, confused, disruptive)
- Attention diffusion modeled as a cellular automaton

**Live Classroom Evaluation** — A camera feed detects average attention levels based on facial expressions using DeepFace emotion detection. This is another data node that could feed back into the simulation to validate and improve it over time.

- Real-time webcam-based emotion detection (DeepFace)
- Per-student engagement tracking
- Timestamped session snapshots
- Summary statistics and timeline analytics

**Test Generator** — An idea we got from a teacher we asked to validate our concepts. She said she would find it useful to have a system that helps identify students who were active during the lesson so they can be rewarded, and creates an exam based on what was said during the class — so students can no longer say *"we didn't talk about this."*

- Upload a recording or paste lesson text
- Automatic transcription via Whisper
- Generates complete assessment bundles: quizzes, practice tests, exams
- Multiple question types, configurable difficulty, language selection
- Bloom's taxonomy alignment
- PDF export

## How We Built It

We used **Claude Code** with our own agent orchestration framework, **dydo**, which coordinated 29 AI agent identities across 111 sessions and 6,930 tool calls — tracked through a full audit system.

**Architecture:**
- **Frontend** — React 19 + TypeScript + Vite + Tailwind CSS v4
- **Backend** — .NET with clean architecture (API → Application → Domain → Infrastructure), orchestrated by .NET Aspire
- **Microservices** — Python FastAPI with RabbitMQ workers for async processing (transcription, assessment generation, emotion detection)
- **Database** — PostgreSQL with PostGIS
- **Message Queue** — RabbitMQ for service communication
- **Deployment** — Azure Kubernetes Service (AKS) with GitHub Actions CI/CD
- **AI** — Azure OpenAI (lesson structuring, test generation), Whisper (transcription), DeepFace (emotion detection)

**By the numbers:**
- 120+ commits, 45 merges across 4 developers
- ~13,000 lines of application code (TypeScript, C#, Python)
- 190K+ total lines added
- 4 Dockerfiles, 7 Kubernetes manifests
- Built in ~18 hours

## Challenges We Ran Into

We had many different ideas and a hard time justifying their co-existence, but in the end they came together as assisting tools before, during, and after the class.

We had a hard time making things work together — we almost bit off more than we could chew. None of the three core features worked until 6 AM. This is partly the reason why we almost managed to type our domain correctly, but as it turns out we messed it up. Spent half an hour debugging it and ended up not correcting it. The realisation came as a funny moment to us and we own it as a wound during the battle against sleep deprivation: **teachersim*a*l*u*tor.hu**

## What We Learned

"Our" best ideas came from other people and not AI. It was a powerful tool, but without a clear vision it could also make our lives a bit harder at times.

We had so many failures we eventually ran out of things which could go wrong.
