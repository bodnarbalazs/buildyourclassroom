---
area: understand
type: concept
must-read: true
---

# Architecture Overview

A classroom dynamics platform orchestrated by .NET Aspire. The AppHost wires up all services, infrastructure, and dependencies — run it and everything starts together.

---

## Project Structure

```
src/
├── backend/
│   ├── Hackathon.AppHost/       # .NET Aspire orchestrator (start here)
│   ├── Hackathon.Api/           # ASP.NET Core Web API
│   ├── Hackathon.Application/   # Business logic / use cases
│   ├── Hackathon.Domain/        # Domain models and contracts
│   ├── Hackathon.Infrastructure/# Data access, external integrations
│   └── Hackathon.ServiceDefaults/# Shared Aspire service configuration
├── frontend/                    # React 19 + TypeScript SPA (Vite, Tailwind v4)
└── microservices/
    └── microservice/            # Python FastAPI service + RabbitMQ workers
```

---

## Key Components

### AppHost (Orchestrator)

The .NET Aspire AppHost (`backend/Hackathon.AppHost/`) is the single entry point. It provisions PostgreSQL (with PostGIS), RabbitMQ, the .NET API, the React frontend, and the Python microservice/worker, wiring all references and health checks automatically.

### .NET API

Clean-architecture backend: Api → Application → Domain, with Infrastructure for persistence. Connects to PostgreSQL and publishes/consumes messages via RabbitMQ.

### React Frontend

React 19 SPA served by Vite on port 3000. Uses React Router, TanStack Query for data fetching, and Tailwind CSS v4 for styling. Tests run with Vitest.

### Python Microservice

FastAPI service (port 8000) managed with `uv`. Includes a RabbitMQ worker process for async task processing. Tests run with pytest.

---

## Data Flow

```
Browser → React SPA (3000) → .NET API (HTTPS) → PostgreSQL (PostGIS)
                                    ↕
                               RabbitMQ ↔ Python Worker
                                    ↑
                         Python FastAPI (8000)
```

---

## Where to Find Things

| Looking for... | Location |
|----------------|----------|
| Service orchestration | `src/backend/Hackathon.AppHost/AppHost.cs` |
| API endpoints | `src/backend/Hackathon.Api/` |
| Business logic | `src/backend/Hackathon.Application/` |
| Domain models / messages | `src/backend/Hackathon.Domain/` |
| Frontend pages / components | `src/frontend/src/` |
| Python API routes | `src/microservices/microservice/api/` |
| Python workers | `src/microservices/microservice/workers/` |

---

## Key Decisions

*Link to decision records in `project/decisions/` for architectural choices.*

---

## Related

- [About This Project](./about.md) — Project description and goals
- [Coding Standards](../guides/coding-standards.md) — Code conventions
- [How to Use These Docs](../guides/how-to-use-docs.md) — Navigating the documentation
