# AI QA Operating System — Monorepo

> A persistent, memory-bearing AI reasoning layer that sits above QA tools (Jira, GitHub, Slack, Playwright).

## Quick Start

### Prerequisites (install manually)
| Tool | Version | Download |
|------|---------|----------|
| **Docker Desktop** | latest | https://docker.com/products/docker-desktop |
| Python | 3.12+ (3.14 works) | already installed |
| Node.js | 22+ (25 works) | already installed |
| uv | latest | auto-installed via setup |
| pnpm | 9.x | auto-installed via setup |

### One-command setup
```powershell
.\scripts\setup.ps1
```

This will:
1. Create Python virtual environment (Python 3.12 via uv)
2. Install all Python dependencies
3. Install all Node dependencies
4. Copy `.env.example` → `.env`
5. Start all infrastructure via Docker Compose (Neo4j, PostgreSQL, MinIO, Temporal)
6. Run database migrations
7. Run all tests

### Start infrastructure only
```powershell
docker-compose up -d
```

### Run tests
```powershell
# All tests
$env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"; uv run pytest

# Specific pack
uv run pytest packages/connector-contract/ -v
uv run pytest packages/kg-client/ -v
uv run pytest services/connectors/ -v
```

### Stop infrastructure
```powershell
docker-compose down
```

---

## Monorepo Structure

```
qa-os/
├── infra/                  # PACK-01: Infrastructure & Repositories
│   ├── neo4j/              # Neo4j 5.26.x Enterprise LTS
│   ├── postgres/           # PostgreSQL 16.x + migrations
│   ├── deploy/             # S3-compatible object storage (MinIO)
│   ├── temporal/           # Temporal durable execution (feature-flagged)
│   ├── litellm/            # Self-hosted LiteLLM gateway
│   └── auth/               # WorkOS tenant setup
├── packages/               # Shared packages (PACK-02, 03, 04)
│   ├── connector-contract/ # Universal connector interface
│   ├── kg-client/          # Knowledge graph client (stub + real)
│   ├── llm-gateway-client/ # LLM gateway wrapper
│   ├── schemas/            # Canonical Pydantic entity types
│   ├── config-service/     # Versioned configuration
│   └── extraction/         # Structured extraction backbone
├── services/               # Runtime services
│   ├── api/                # Backend API layer
│   ├── connectors/         # Tool adapters (Jira, GitHub, Slack, Playwright)
│   ├── orchestrator/       # LangGraph orchestration backbone
│   └── graph-service/      # Knowledge graph construction
├── modules/                # PACK-06 through 09: Reasoning modules
│   ├── module-01/          # Requirement Risk Assessor
│   ├── module-02/          # Test Suite Generator
│   ├── module-03/          # Human Review Gate
│   ├── module-04/          # Execution Orchestrator
│   ├── module-05/          # Defect Triage
│   ├── module-06/          # Release Readiness
│   ├── module-07/          # Knowledge Surface (queries)
│   ├── module-08/          # Feedback Loop
│   └── module-09/          # Command Center (dashboard)
├── apps/
│   └── web/                # PACK-10: Next.js frontend (Command Center)
├── .ci/                    # CI/CD configurations
├── .lint/                  # Custom lint rules
├── docs/                   # Operational documentation
├── scripts/                # Setup and utility scripts
├── pyproject.toml          # Python workspace root
├── pnpm-workspace.yaml     # Node workspace
├── docker-compose.yml      # Local dev infrastructure
└── .env.example            # Environment variables template
```

## Sprint Map

| Sprint | Pack | Focus |
|--------|------|-------|
| 0 | PACK-01, 02, 03 | Foundation: infra, connectors, core abstractions |
| 1 | PACK-02 | Module 10: Connector adapters |
| 2 | PACK-04 | Module 7 Substrate: Knowledge graph |
| 3-4 | PACK-06 | Module 1 & 2: Reasoning logic |
| 5-6 | PACK-07 | Module 3 & 4: Pipelines |
| 7-8 | PACK-08 | Module 5 & 6: Triage services |
| 9-10 | PACK-09 | Module 7 Surface & Module 8: Loops |
| 0-11 | PACK-10 | Module 9: Dashboard (continuous) |
| 11 | PACK-05, 11 | Security, evaluation, hardening |

## Technology Stack (pinned)

| Component | Technology | Version |
|-----------|-----------|---------|
| Python | CPython | 3.12 |
| Node | Node.js | 22.x LTS |
| Graph DB | Neo4j Enterprise LTS | 5.26.x |
| Relational DB | PostgreSQL | 16.x |
| Object Storage | MinIO (S3-compat) | latest |
| LLM Gateway | LiteLLM | pinned tag |
| Orchestration | LangGraph | 1.2.x |
| Durable Exec | Temporal | (feature-flagged) |
| Auth | WorkOS | (buy-not-build) |
| Protobuf | protobuf | ≥4.x |
| Schema validation | Pydantic | 2.x |
| Test framework | pytest | 8.x |
| Evaluation | DeepEval + RAGAS + Promptfoo | pinned |
