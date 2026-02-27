# Hackathon Template

Full-stack hackathon starter template with .NET Aspire orchestration, React + Vite + TypeScript frontend, Python FastAPI microservice, and clean-architecture .NET backend.

## Quick Start

```bash
dotnet run --project src/backend/Hackathon.AppHost
```

This launches the Aspire dashboard with all services:
- **API** (.NET) — ASP.NET Core with OpenAPI + Scalar
- **Frontend** (React) — Vite dev server with Tailwind CSS
- **Microservice** (Python) — FastAPI with uvicorn

## Project Structure

```
src/
  backend/
    Hackathon.AppHost/          # Aspire orchestrator
    Hackathon.ServiceDefaults/  # Shared telemetry & health checks
    Hackathon.Api/              # ASP.NET Core API
    Hackathon.Domain/           # Domain models (no dependencies)
    Hackathon.Application/      # Business logic layer
    Hackathon.Infrastructure/   # Data access & external services
  frontend/                     # React + Vite + TypeScript + Tailwind
  microservices/
    microservice/               # Python FastAPI
tests/
  backend/                      # xUnit test projects
```

## Prerequisites

- [.NET 10 SDK](https://dotnet.microsoft.com/download)
- [Node.js 20+](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Development

### Build & Test (.NET)

```bash
dotnet build Hackathon.slnx
dotnet test Hackathon.slnx
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev      # Dev server
npm run build    # Production build
npm test         # Run tests
```

### Python Microservice

```bash
cd src/microservices/microservice
uv sync
uv run pytest
```

## Optional Infrastructure

The AppHost has commented-out blocks for common infrastructure. To enable:

1. Uncomment the NuGet package in `Hackathon.AppHost.csproj`
2. Uncomment the resource block in `AppHost.cs`
3. Add `.WithReference(...)` to wire it to your services

Available: **PostgreSQL**, **Redis**, **RabbitMQ**, **Neo4j**
