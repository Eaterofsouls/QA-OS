# AI QA Operating System

> **An AI system that scores how risky a software requirement is, drafts test cases for it, and remembers what a human decided the next time something similar comes up.**

- **Live Companion Platform & Showcase:** [qa.buildwithdaksh.com](https://qa.buildwithdaksh.com)
- **Author:** Daksh Chauhan ([buildwithdaksh.com](https://buildwithdaksh.com))
- **License:** MIT

This README explains the project in plain language first, then gets precise about exactly what's real, what's broken, what's empty, and what's still just a plan. Nothing in this repository has been deleted or tidied away to make it look more finished than it is — if a file is a one-line stub, it's still here, and it's labeled as one.

Two companion documents go deeper:
- **[VISION.md](./VISION.md)** — the problem, the full ten-module lifecycle this is aiming at, and why it's built this way.
- **[GUIDANCE.md](./GUIDANCE.md)** — engineering principles for anyone extending this code, plus specific ways to contribute (four kinds of collaborator, four specific asks).

---

## The short version

Software teams re-derive the same QA judgment over and over: how risky is this change, what should we test, has something like this broken before. That reasoning usually lives in a person's head, a Slack thread, or a closed ticket — and it evaporates the moment that person moves on. This project's bet is that an AI system can absorb the repetitive part of that reasoning (drafting a risk score, drafting test cases) while a human keeps the part that actually requires judgment (deciding what ships) — and, critically, that the system should *remember* what was decided, so the next similar case doesn't start from zero.

**What that looks like in five steps, today, for real:**

1. **A requirement comes in.** Someone writes what needs to be true, in plain English — e.g. "Users must be able to log in via OAuth2, including token refresh and session expiry."
2. **Risk gets scored, by AI.** The system looks up similar requirements it has seen before, then scores this one's risk (0-1) and writes down why.
3. **Tests get drafted, by AI.** Candidate test cases are generated from the requirement and its risk score. They're marked `draft` — nothing is trusted yet.
4. **A person decides.** A QA lead approves or rejects each draft test. No model makes this call. This is the one step with no AI in it at all.
5. **The decision is remembered.** Whatever the person decided is written back to storage, so the next similar requirement inherits it instead of starting cold.

That loop — steps 1 through 5 — is real. It runs over actual HTTP, against a real (or your own) LLM, with a real human-approval gate in the middle. Everything past step 5 — actually running the generated tests, triaging a failure, deciding if a release is ready to ship — is the direction this project is headed, not something it can do yet. The rest of this document is about being exact regarding that line.

---

## Table of Contents
1. [What This Repository Is](#1-what-this-repository-is)
2. [Repository Map](#2-repository-map)
3. [How to Run It](#3-how-to-run-it)
4. [Module-by-Module Status — all ten, none hidden](#4-module-by-module-status--all-ten-none-hidden)
5. [Package & Service Status](#5-package--service-status)
6. [Known Limitations, Stated Plainly](#6-known-limitations-stated-plainly)
7. [Changelog](#7-changelog)
8. [FAQ](#8-faq)

---

## 1. What This Repository Is

Two layers, kept deliberately separate:

- **`/docs`** — a complete research and specification library: a domain model, a frozen engineering spec (with its own internal red-team review), a sprint roadmap, scope-decision records, and four research surveys (market landscape, AI-feasibility, standards/compliance, tooling). This is the "why" and the "full plan." It is internally consistent and was pressure-tested against three professional personas during design — but that pressure-testing was one reasoning process checking its own output, not outside review by a real QA professional with nothing at stake. Read [VISION.md](./VISION.md) for the substance of this layer.
- **`/src`** — the actual code. A Python monorepo (`uv` workspace) for the backend plus a Next.js frontend, structured as `apps/` (frontend), `packages/` (shared libraries), `modules/` (the ten reasoning modules from the spec), `services/` (the HTTP API, external connectors, and two stub services), and `infra/` (Docker Compose, Terraform, SQL migrations — fully configured, mostly unexercised).

**By the numbers, honestly:** of the ten modules the spec describes, three are real and wired end-to-end, two more have real logic sitting behind no route yet, one has a single real-but-unwired integration adapter, and four are stubs or broken. Section 4 below has the specifics for every single one — not just the good ones.

---

## 2. Repository Map

```
docs/                      the specification library (see VISION.md)
src/
  apps/web/                Next.js 14 frontend -- the "Command Center"
  packages/
    kg-client/             storage abstraction -- 3 backends behind 1 interface
    llm-gateway-client/    the one permitted path to any LLM provider
    extraction/            structured-output validation layer
    connector-contract/    the protocol every external adapter must satisfy
    schemas/               entity models -- currently empty scaffolding
    config-service/        empty scaffolding
    rendering/             empty scaffolding
    evaluation/            empty scaffolding
  modules/
    module-01/             Risk Assessor             -- real, wired
    module-02/             Test Generator            -- real, wired
    module-03/             Review Gate               -- real, wired
    module-04/             Execution Orchestrator    -- exists, broken, unwired
    module-05/             Defect Triage             -- real logic, unwired
    module-06/             Release Readiness         -- real logic, unwired
    module-07/             KG Query Surface          -- stub
    module-08/             Production Feedback Loop  -- stub
    module-09/             QA Command Center backend -- stub
  services/
    api/                   FastAPI -- the real HTTP layer, 6 live routes
    connectors/
      jira/                real, substantial adapter -- unwired
      github/ slack/ playwright/ legacy/   one-line stub adapters
    graph-service/         stub
    orchestrator/          stub
  infra/                   Docker Compose, Terraform, migrations -- configured, mostly unexercised
```

Every stub above is a real file in this repository right now. None of them were deleted to make this list shorter.

---

## 3. How to Run It

### Prerequisites
- Python 3.12+, [`uv`](https://docs.astral.sh/uv/)
- Node 18+, `npm`
- An OpenAI-compatible LLM API endpoint and key (a direct provider, or a LiteLLM gateway -- `docker-compose.yml` provisions one)

### Backend
```bash
cd src/services/api
uv sync
export LITELLM_BASE_URL=https://api.openai.com/v1   # or your gateway / other provider
export LITELLM_API_KEY=sk-...
uv run uvicorn main:app --reload
```
Verify: `curl localhost:8000/health` returns `{"status":"ok","kg_backend":"KGClientStub"}`

### Keep demo data across restarts (optional)
The default storage backend, `KGClientStub`, is an in-memory dict -- restart the process and everything is gone. Point `KG_SQLITE_PATH` at a file to use the SQLite-backed implementation of the same interface instead:
```bash
export KG_SQLITE_PATH=./kg_data.sqlite3
```
This is genuinely persisted (see `services/api/verify_step7_sqlite_persistence.py`, which proves it across two separate process runs -- not just a before/after check in the same process) but it is **not** a real graph database: one table, no edges, no query planner, no Cypher.

### Frontend
```bash
cd src/apps/web
npm install
npm run dev
# open http://localhost:3000
```
Type a requirement into "Run Requirement Pipeline" and click **Assess & Generate Tests**. Once test cases appear, "Pending Review" lets you approve or reject each one -- that's Module 3, running for real.

### Full infra (optional -- not required for anything above)
```bash
cd src
docker-compose up   # Neo4j 5.26 Enterprise, Postgres 16, MinIO, Temporal + UI, a LiteLLM gateway
```
Setting `NEO4J_URI` afterward switches the storage backend to real Neo4j -- no code changes required, same interface. This path exists in the code and has never been exercised against a live Neo4j instance in this environment. That's worth repeating plainly: it's written, not proven.

### One packaging thing worth knowing before you edit source
`kg-client`, `llm-gateway-client`, `extraction`, and `module-01/02/03` install as **non-editable** packages. Editing their source doesn't take effect until you run:
```bash
uv sync --reinstall-package kg-client   # or whichever package you edited
```
Forgetting this is the single most likely reason a change "doesn't do anything."

---

## 4. Module-by-Module Status -- all ten, none hidden

| # | Module | What it's supposed to do | Status | The actual detail |
|---|---|---|---|---|
| 1 | Requirement Risk Assessor | Score a requirement's risk | Real, verified | Real Pydantic I/O, a real LLM call through the extraction backbone, real persistence. Wired to `POST /requirements/{id}/assess`. Before building its prompt it pulls the top-3 similar past requirements for the tenant (TF-IDF cosine similarity >=0.2, stdlib only, no embeddings) and injects their stored risk level and real human review decision as context. This is retrieval-augmented *prompting* -- there is no model training or fine-tuning anywhere in this repo. |
| 2 | Test Suite Generator | Draft test cases from a requirement + its risk score | Real, verified | Same pattern as Module 1; reads the risk assessment back from storage first. Wired to `POST /requirements/{id}/generate-tests`. |
| 3 | Review Gate | A human approves or rejects generated tests | Real, verified | Real persistence of a real human decision. No model call -- this module is 100% deterministic code plus a person. Wired to `GET /requirements/{id}/tests` and `POST /requirements/{id}/tests/{test_case_id}/review`. |
| 4 | Execution Orchestrator | Run the approved tests via Playwright, orchestrated through Temporal | Exists, broken | `orchestrator.py` is in this repository and it doesn't work: it hardcodes `passed=1` for every test regardless of outcome, and has an unfixed `NameError` (calls `uuid.UUID(...)` without importing `uuid`). `temporal_workflow.py` is a one-line stub, despite Temporal being fully provisioned in `docker-compose.yml`. **This is left visibly broken on purpose, not deleted or hidden**, so the gap is obvious to anyone reading the code. It's first on the roadmap for exactly that reason -- nothing downstream of execution can be trusted until this is real. |
| 5 | Defect Triage | Classify a test failure using stored context | Real logic, unwired | `triage.py` has a genuine (if simple) LLM call behind the correct schema. No route calls it yet. |
| 6 | Release Readiness Advisor | Recommend go/no-go for a release | Real logic, unwired | Same tier as Module 5. `report_generator.py` is empty. |
| 7 | Knowledge Graph Query Surface | Answer natural-language questions over stored QA history | Stub | `query_service.py` calls a hardcoded placeholder id; nothing in storage ever creates the thing it queries. `graphiti_placeholder.py` is a one-line stub. |
| 8 | Production Feedback Loop | Feed real production telemetry back into risk scoring | Stub | `feedback.py` has a plausible shape but no telemetry source exists anywhere to feed it real data. |
| 9 | QA Command Center backend | Serve the frontend's backend surface | Stub | `api_routes.py` is a bare `APIRouter()` with zero routes. The real frontend (`apps/web/`) doesn't use this module at all -- it talks directly to `services/api`. |
| 10 | Integration & Extensibility Layer | Wire Jira/GitHub/Slack/Playwright into the pipeline | One real adapter, unwired | `services/connectors/jira/adapter.py` is genuinely substantial -- 369 lines, real Basic Auth, a real ticket-translation layer. The GitHub, Slack, and Playwright adapters are one-line stub classes with no logic behind them. None of the four are called from any live route yet. |

**Net: 3 of 10 modules are real and wired (1, 2, 3). Two more (5, 6) have real logic with no route calling them. Module 10 has one real adapter (Jira) with nothing wiring it in. Modules 4, 7, 8, 9 are broken or empty, and stay in the repository exactly as they are -- visibly, not quietly.**

---

## 5. Package & Service Status

| Package / Service | Real? | Notes |
|---|---|---|
| `packages/kg-client` | Yes | In-memory stub with real traversal logic and real tenant isolation. Real Neo4j driver code exists but is unexercised without a live Neo4j instance. `create_relationship`/`vector_search`/`hybrid_search` are honest no-ops with `TODO`s, not fakes. TF-IDF similarity search (stdlib only) powers retrieval memory. SQLite backend implements the same interface, selected via `KG_SQLITE_PATH`. |
| `packages/llm-gateway-client` | Yes | Real `httpx` calls to an OpenAI-compatible endpoint. Raises a real error on failure instead of swallowing it. Real SQLite-backed cost ledger, with an honest `null`-vs-`0` distinction for missing data. `cost_ceiling.py` is an explicit, undisguised empty stub -- nothing currently blocks a call for being over budget. |
| `packages/extraction` | Yes | Real JSON-parse-and-validate round trip against a Pydantic schema; raises a typed error on mismatch instead of returning an unvalidated guess. Logs real token usage to the cost ledger, isolated in its own try/except so a logging failure can never break a real response. |
| `packages/connector-contract` | Yes | The most thoroughly tested package in the repository -- a generic, reusable contract-test suite any future adapter can be run against, plus real assertion-based unit tests. |
| `packages/schemas`, `packages/config-service` | No | Empty classes -- `class X(BaseModel): pass`, verbatim. Declared as dependencies but not used by any real logic. Dead weight, not deception: nothing pretends these do something they don't. |
| `packages/rendering`, `packages/evaluation` | No | No real content. |
| `services/api` | Yes | Six real, dependency-injected routes with honest HTTP error codes (404/409/422/502) instead of silent failure. No authentication -- `auth/stub_check.py` is a one-line placeholder that enforces nothing. |
| `services/connectors/jira` | Yes | Real, production-quality async client. Not wired into the live pipeline, but genuinely solid code. |
| `services/connectors/github`, `slack`, `playwright`, `legacy` | No | One-line stub classes. |
| `services/graph-service`, `services/orchestrator` | No | No real content, despite Temporal being fully configured in `docker-compose.yml`. |
| `apps/web` | Yes | A real, typed client (`lib/api.ts`) covering all six live routes. The "Pending Review" panel re-reads status from storage after every click rather than assuming success. The graph explorer (`graph/page.tsx`) is a real `reactflow` view of `GET /requirements/{id}/graph`'s real data. |

---

## 6. Known Limitations, Stated Plainly

- **No real LLM call has ever been made through this pipeline in this environment.** Every verification pass here used a mocked client or a local stand-in HTTP server. The code path is proven; response *quality* from a real model is not.
- **There is no authentication.** Anything that can reach the API can do anything the API allows.
- **There is no cost ceiling.** Usage is logged, honestly, but nothing stops an over-budget call.
- **Retrieval memory only feeds Module 1.** Test generation and defect triage don't use it yet.
- **The Neo4j backend is unexercised.** Real driver code, correct interface, never run against a live database here.
- **There's no automated way to tell if a prompt change made things better or worse** -- only that it changed something. `packages/evaluation` is empty, not just unwired.
- **Module 4 is broken**, not absent -- see Section 4. Nothing downstream of it should be trusted yet.
- **Three of four connector adapters are one-line stubs.** Only Jira has real logic behind it, and even Jira isn't wired into a live route.

---

## 7. Changelog

The short version of how this moved from "generated in bulk, never actually run" to "a verified working slice":

1. `kg-client/stub.py`'s `get_related()` was hardcoded to return `[]`. Rewritten to genuinely traverse in-memory nodes.
2. `llm-gateway-client` and `extraction` both silently caught every failure and returned a fake "successful" empty result. Both now raise real, typed errors.
3. A `uv sync` failure that looked like a dependency problem turned out to be a missing `[tool.hatch.build.targets.wheel]` section in nearly every `pyproject.toml` in the monorepo -- meaning most packages had likely never been importable at all, which explained a pattern already visible elsewhere in the repo (empty test stubs that "pass" without testing anything). Fixed at the root cause, not patched around.
4. A SQLite-backed storage implementation was added behind the existing `KGClientInterface` with zero changes to any caller -- the interface was actually swappable, not swappable-in-theory.
5. A two-process verification script (`verify_step7_sqlite_persistence.py`) was written specifically because a same-process before/after check doesn't actually prove persistence survives a restart -- only that Python's own memory didn't get cleared.

---

## 8. FAQ

**Is this in production anywhere?** No. This is a personal, solo-built project.

**Has a real LLM ever actually scored a real requirement through this code?** The code path has -- through mocks and a local stand-in server. A live provider key has not been used against this pipeline in this environment. That's stated as plainly as possible on purpose.

**Why keep Module 4 in the repo if it's broken?** Because a broken module you can see is a known problem. A broken module that's been deleted is a problem someone else discovers the hard way. The second one is worse.

**Can I use the Jira adapter?** The code is real and solid, but nothing in `services/api` currently calls it. You'd be wiring it in yourself.

**Where do I start if I want to help?** See [GUIDANCE.md](./GUIDANCE.md) -- it has specific entry points for QA engineers, applied AI/LLM engineers, backend/platform engineers, and engineering leaders who want to pilot this against a real backlog.
