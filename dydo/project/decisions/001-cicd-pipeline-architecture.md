---
type: decision
status: accepted
date: 2026-02-27
area: infrastructure
---

# 001 — CI/CD Pipeline Architecture

## Context

We need a deployment pipeline for a polyglot Aspire app (6 services) targeting Azure. Constraints: $20 budget, 15-hour hackathon, fast deploy cycles matter more than production-readiness.

## Decision

### Infrastructure: Terraform (minimal)

Create AKS + ACR with ~80 lines of Terraform. Enables `terraform destroy` for clean teardown and reproducible setup. No portal clicking.

- 1x B2ms node (2 vCPU, 8GB RAM) — ~$0.08/hr
- ACR Basic tier
- Estimated total cost: ~$2-3 for the hackathon

### Kubernetes manifests: aspirate (with fallback)

Use `aspirate generate` to produce k8s manifests from the Aspire AppHost. If aspirate struggles with the Python services, fall back to hand-written YAML for those specific services.

### Container images: Dockerfiles per service

Write Dockerfiles for: API, frontend, microservice, worker. Required regardless of whether aspirate or hand-written k8s manifests are used.

### Databases: in-cluster containers

Postgres and RabbitMQ run as containers inside AKS, matching the local dev topology. No managed services — saves money and setup time.

### Deploy trigger: git tags

`git tag v1.0.0 && git push origin v1.0.0` triggers GitHub Actions.

### Two deploy paths

1. **Local `deploy.sh`** — fast path during hackathon (~1-2 min with Docker cache)
2. **GitHub Actions on `v*` tags** — official pipeline for demo/presentation

## Alternatives Considered

- **Terraform for everything** — Too heavy. App deploys don't belong in Terraform.
- **No Terraform (portal/CLI only)** — Can't reliably destroy and recreate. Risk of leaked credits.
- **`azd` for deployment** — Good Aspire integration but opinionated. Less control when debugging at 2am.
- **Azure Container Apps instead of AKS** — Awkward for stateful containers (Postgres, RabbitMQ).
- **Managed databases** — $3-5/day extra, unnecessary for a hackathon.
- **Hand-written k8s YAML only** — Fallback option if aspirate fails. More upfront work but fully predictable.

## Consequences

- Fast, reproducible infra setup and teardown
- Deploy speed optimized for hackathon iteration
- Clean demo story: "we tag a version, it deploys automatically"
- If aspirate-generated manifests misbehave, agent (Adele) debugs or falls back to hand-written YAML
