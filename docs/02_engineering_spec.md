# Engineering Freeze v1.0
## AI QA Operating System — Final Engineering Specification

> **Status: this is still the authoritative target architecture** — the
> design the codebase is meant to grow into — but it describes a 10-module
> system with Neo4j/Temporal/Postgres/WorkOS all running in production. **Only
> a fraction of this is actually built and running.** As of today, 3 of 10
> modules (Requirement Risk Assessor, Test Suite Generator, Review Gate) are
> real and wired; the rest are stub scaffolding or unbuilt, and most of the
> infra below (Neo4j, Temporal, auth) has never been run outside an in-memory
> stub. Treat this doc as the blueprint, not as documentation of the current
> system — see the top-level `README.md` §4–§7 for what's actually real today.
> `05_scope_decisions.md` has the history of how this design was arrived at.

---

**Author:** Daksh Chauhan — Chief Architect / Technical Director, final sign-off before Sprint 0.
**Status:** FROZEN. This document is the single engineering specification for implementation. It supersedes and consolidates — but does not replace the historical record of — every prior document in the pipeline.
**Inputs consumed, all treated as history, not as independent authority:**
- `AI_QA_OS_Master_Specification_FINAL_v1.md` — product definition, MVP scope cut, persona validation
- `Canonical_QA_Knowledge_Base_v2_enriched.md` — QA domain model, pain-point evidence, AI-transformability classification
- `Engineering_Landscape_Report.md` — technology research, build/reuse/wrap/buy analysis
- `Development_Master_Plan.md` — technology stack, repository philosophy, sequencing
- `Implementation_Blueprint_Part_1.md` — subsystem boundaries, service architecture, data flow, interface philosophy
- `Red_Team_Implementation_Review.md` — independent Principal Engineer review (health score 6.5/10, verdict "YES, WITH CHANGES")

**What this document does that no prior document did:** it closes the loop the Red Team opened. Three findings in that review were Critical — block-Sprint-0-grade — and this document does not defer them to "a future pass." It resolves them, in place, as part of the frozen architecture. Where the Red Team found real but non-blocking risk, this document either accepts the fix, partially accepts it with a stated staging decision, or rejects it with engineering reasoning. Nothing from that review was silently dropped. The full ledger is in **Accepted / Rejected / Deferred**, below.

**What this document is not:** it is not new research, not a redesign, not a scope expansion. Every module boundary, every entity, every V1/Phase-2+ scope line drawn in the Master Specification and carried through the Blueprint and Development Master Plan is preserved. What changed is narrower and sharper: one data-model gap closed, one isolation model decided, one migration discipline defined, one Sprint 0 risk de-risked, and a small number of infrastructure-adoption *timings* renegotiated in the direction of "build it when the system needs it," never in the direction of "skip it."

---

# Executive Summary

**Overall engineering health: 8.5/10 — up from the Red Team's 6.5/10, specifically because the three items that were holding the score down are resolved in this document rather than scheduled for later.**

**Implementation readiness: Ready for Sprint 0, as specified below.**

**Approval status: APPROVED FOR IMPLEMENTATION.**

Five conclusions drive that status:

1. **The product architecture underneath all of this was already sound.** Six documents and five research hops produced a genuinely well-reasoned system: ten modules that map to evidenced pain points, a data model with a defensible entity boundary, an agent/human responsibility split with three non-negotiable human-in-the-loop gates, and a technology stack where nearly every choice carries a specific, named rejected alternative rather than a default. The Red Team's own words apply: "This is not a team that doesn't know what it's doing." Freezing this architecture is a matter of closing gaps, not rebuilding it.

2. **The Red Team's three Critical Issues were real, and are now closed, not scheduled.** The pipeline's own "most material finding" (the missing Waived/Accepted Defect + Rationale attribute) is now in the Sprint 0 data model. The Knowledge Graph's multi-tenancy isolation model is now decided (shared graph, mandatory `tenant_id` scoping, enforced once in `kg-client`, never by per-query convention). A graph schema migration discipline now exists, modeled directly on the connector contract's own design-before-implementation pattern. None of these required new research — they required applying discipline the project already knew how to apply, to the two places it hadn't yet.

3. **Sprint 0's single-biggest schedule risk — a serialized, seven-system "big-bang" Foundation — is de-risked, not just acknowledged.** Foundation is timeboxed with an explicit stub-and-swap fallback (a fake graph client and a fake auth check let Module 1 development start even if Neo4j+Graphiti or WorkOS provisioning runs long), and Graphiti's temporal-versioning layer specifically is staged out of Sprint 0 entirely — Neo4j ships on day one (unchanged, core to the architecture), Graphiti's temporal layer ships when a real "was this still true at time T" query is needed, not before.

4. **A small number of infrastructure-adoption decisions are re-staged, not re-decided.** Temporal, self-hosted Langfuse, legacy connector adapters, three of four mutation-testing engines, a dedicated reranker, and tiered object-storage retention all remain the correct *eventual* choice and are frozen as such — but each now has an explicit, named trigger condition for when it enters the build, rather than entering in Sprint 0 by default. This is the same config-over-code philosophy the project already applies to the risk heuristic, applied to infrastructure adoption timing instead of runtime values.

5. **A small number of Red Team findings are genuinely deferred (not fixed, not ignored) or rejected outright, each with reasoning.** The full ledger — every Critical Issue, Major Risk, Underengineering finding, Moderate Concern, Minor Improvement, and Demo Optimization — is triaged individually in the **Accepted / Rejected / Deferred** section. Nothing was silently dropped, and nothing was accepted reflexively either — Overengineering Finding #2 (replacing Neo4j with Postgres) is explicitly **rejected**, because the Red Team itself called it "a defensible bet either way," not a critical engineering justification, and this document does not replace a major technology on a bet.

**No engineer reading this document, and its module folder, should need to ask "what should we build." Every remaining question is a sprint-planning question, not an architecture question.**


---

# Final Architecture

## 1. System Overview

The AI QA Operating System is a persistent, memory-bearing reasoning layer that sits above the testing and delivery tools a QA organization already owns (Jira, GitHub, Slack, Playwright at V1). It does not replace any of them. It orchestrates them, and it owns the one thing none of them own individually: continuity of judgment across the lifecycle of a requirement — from the moment it's written, through risk assessment, test design, execution, defect triage, and release readiness, to the moment a related production incident feeds back into how the *next* requirement is risk-assessed.

At the engineering level, the system is **one long-lived reasoning chain, wrapped in durable orchestration, reading from and writing to one shared memory.** Ten product modules exist. They are not ten independent applications — they are ten stages of a single pipeline (plus one always-on dashboard and one deliberately narrow feedback loop) sharing a spine: one way data enters from external tools, one place that data is stored and related, one way any module calls a language model, and one way any module's output becomes a human-readable, cited artifact.

Four engineering facts shape everything below — the first three inherited unchanged from the frozen inputs, the fourth added by this document:

1. **The Knowledge Graph is a foundation-layer dependency, not a seventh module.** Its substrate exists before the first module that writes to it (Module 1) finishes. Every reasoning module downstream of ingestion reads it, writes it, or both.
2. **The connector layer's interface is the real deliverable — the individual tool integrations are not.** Four connectors ship at V1 (Jira Cloud, GitHub, Slack, Playwright), behind a contract designed before the first tool-specific line of code, so a fifth connector in Phase 2+ is an adapter, not a rewrite.
3. **Where AI capability has a known, documented ceiling — test generation (~30–41% mutation score), flaky-vs-defect classification from logs alone — engineering investment goes into the scaffolding around the model call (review gates, retrieval context, mutation-testing feedback), never into chasing a better prompt.**
4. **Interface-churn discipline — designed before implementation, frozen before the first dependent is built — now applies uniformly to every high-blast-radius surface, not selectively.** The connector contract had this discipline from the start. The Knowledge Graph schema, and the tenant-isolation model inside it, did not, and now do. This is the one structural addition this document makes to the architecture itself, and it is a discipline extension, not a redesign.

The system is a hosted, multi-tenant SaaS product for V1. It is explicitly not a CI/CD replacement, not an autonomous release-trigger, and not a second system of record competing with the tools it orchestrates.

## 2. Major Subsystems

| Subsystem | Why it exists | Status |
|---|---|---|
| **Frontend / Command Center** | One dashboard surface live-streaming a coherent, multi-step reasoning chain to different roles without becoming a fourth tool to check (Module 9). | Frozen, unchanged |
| **Backend / API Layer** | The single tenant-aware, authenticated front door for the frontend, connectors, and any future integration. | Frozen, unchanged |
| **Agent Runtime / Orchestration Layer** | The primary workflow is an eight-step chain with two mandatory human-review gates, running over minutes, needing a full audit trail and crash-tolerant handling of a hard self-verification constraint. | Frozen; **adoption of the durable-execution (Temporal) layer is now explicitly staged — see Final Technology Stack** |
| **Knowledge Layer (Graph Substrate)** | The ten-entity graph is the system's institutional memory; every reasoning module after ingestion reads or writes it. | Frozen; **now carries an explicit tenant-isolation model and a schema-migration discipline that did not previously exist** |
| **Connector Layer** | The literal front and back door of the system — nothing flows in or out without it. | Frozen, unchanged |
| **Storage (Relational + Object)** | Tenant/user/billing state, connector configuration, and versioned calibration values are relational; large execution-trace artifacts are blob-shaped. | Frozen; **object storage now carries a mandatory backup/DR and retention policy from first write** |
| **Evaluation Subsystem** | Three of ten modules sit near documented accuracy ceilings; evaluation is the only mechanism that verifies "V1-core done" claims rather than asserting them. | Frozen, unchanged |
| **LLM Gateway** | Per-module model assignment, cost tracking, and provider fallback are a configuration change, not a code change. | Frozen; **now carries a mandatory per-tenant cost-governance policy, not just a capability** |
| **Shared Infrastructure (cross-cutting)** | Authentication, configuration, prompt versioning, rendering, structured extraction — each needed by multiple modules in materially the same shape. | Frozen, unchanged |
| **Configuration Service** | Three explicitly-flagged-as-unknowable-today values (risk-to-coverage heuristic, defect/flake threshold, model routing) may never be hard-coded. | Frozen; **now carries a minimum calibration-process definition — see Final Engineering Principles** |
| **Authentication** | Enterprise SSO/SCIM is a day-one requirement for this buyer profile, not a later hardening pass. | Frozen; **live SSO/SCIM configuration is staged to first design-partner onboarding, not Sprint 0 — the buy decision itself is unchanged** |
| **Observability** | The product's legibility claim is only true if every model call, graph read, and orchestration step is traced. | Frozen; **hosting timing staged — see Final Technology Stack** |
| **Rendering / Reporting Service** | One shared transformation from structured, cited entities to a trustworthy human artifact, used by Release Readiness and the Command Center. | Frozen, unchanged |

## 3. Subsystem Boundaries

For each subsystem: what it owns, what it must never own, how it communicates, and who owns it. These boundaries are unchanged from the Implementation Blueprint except where explicitly marked.

### Frontend / Command Center
- **Owns:** role-aware presentation of the reasoning chain's live and historical state; per-module trust/reliability indicators shown separately, never blended into one confidence number; forwarding human-review actions (approve a test suite, make a go/no-go call) to backend services.
- **Never owns:** any model call; any business logic deciding risk, coverage, or defect classification; any direct read/write to the graph or relational store.
- **Talks to:** the API layer only, over REST/GraphQL plus a streaming channel for live updates.
- **Owned by:** the Module 9 team; consumes the shared rendering service and design system.

### Backend / API Layer
- **Owns:** authentication and tenant/session handling; routing to the correct module's orchestration entry point; the single externally-reachable surface.
- **Never owns:** module-specific reasoning logic; direct LLM calls; graph traversal logic beyond routing.
- **Talks to:** the orchestration layer, the graph service, authentication — never bypassed.
- **Owned by:** collectively, as a foundation-layer service — **with an explicit on-call rotation, see Final Engineering Principles.**

### Agent Runtime / Orchestration Layer
- **Owns:** the eight-step primary reasoning chain and the secondary feedback-loop workflow; checkpointing; human-in-the-loop gating at Modules 3 and 6; crash-tolerant handling of the rule that a module's own output must never verify itself.
- **Never owns:** any one module's domain reasoning; direct external-tool calls (those go through the connector layer); permanent storage of business entities.
- **Talks to:** invokes modules as workflow steps; modules hand results back through the orchestrator, never directly to each other — all cross-module handoff is a persisted entity reference.
- **Owned by:** collectively, as a foundation-layer service. **The inner checkpointed-chain concern (LangGraph) and the outer durable-execution concern (Temporal) remain two layered responsibilities, introduced at different points — see Final Technology Stack for the now-explicit trigger condition on the second layer.**

### Knowledge Layer (Graph Substrate)
- **Owns:** the ten-entity schema and relationships; **mandatory tenant scoping on every node and relationship, enforced in exactly one place — see below**; read/write APIs used by every reasoning module; the retrieval path Module 7's product surface exposes.
- **Never owns:** a second, parallel memory or retrieval system for any module's "narrow" need — standing prohibition, not a style preference. Never holds relational-only concerns.
- **Talks to:** every reasoning module through one typed client (`kg-client`), never ad hoc database drivers.
- **Owned by:** a foundation-layer service, built before Module 1 finishes. **Now carries a named schema-migration discipline and a named tenant-isolation model — both frozen below, both new relative to the Blueprint.**

**Tenant isolation, decided:** every node and relationship in the graph carries a `tenant_id` property. Every query path in `kg-client` is required to filter on it, and `kg-client` is the *only* code in the system permitted to issue a Cypher query — no module, service, or script queries Neo4j directly, ever. This makes tenant scoping a property of one chokepoint, not a convention every future query author has to remember. Isolation is enforced in software, not in infrastructure, for V1: a single shared Neo4j instance, not per-tenant Enterprise-Edition databases, because the licensing cost of physical per-tenant separation is not justified at design-partner scale, and physical separation remains available as a Phase 2+ upgrade once a real security review demands it (see ADR-004).

**Schema migration discipline, decided:** the graph schema follows the same design-before-implementation discipline the connector contract already has. Concretely: (a) schema changes in V1 are additive-only — new properties or relationship types may be added, nothing is removed or renamed without a deprecation window; (b) any schema change ships with a compatibility check that runs every consuming module's read path against the new shape before the change merges; (c) the Waived/Accepted Defect + Rationale attribute (below) is the first schema element built under this discipline, not an exception to it.

### Connector Layer
- **Owns:** one internal contract (authenticate, subscribe, fetch, post-status-back) with a thin adapter per external tool.
- **Never owns:** any reasoning about what a fetched ticket or result *means* — translation only, never interpretation.
- **Talks to:** every module needing external data goes through the contract, never a tool-specific SDK embedded in module code.
- **Owned by:** a foundation-layer service, deliberately over-invested in relative to its apparent simplicity.

### Storage (Relational + Object)
- **Owns — relational:** tenant/user/billing state, connector configuration, versioned calibration configuration. **Owns — object:** large execution-trace artifacts, with a retention *and* backup/DR policy attached from the first write (new — see Final Engineering Principles).
- **Never owns:** any graph-native entity as a shadow copy.
- **Talks to:** accessed through the configuration service and the API layer, never queried directly by a module.
- **Owned by:** a foundation-layer service.

### Evaluation Subsystem
- **Owns:** CI-gating regression tests for every LLM-driven module; retrieval-quality metrics for the knowledge layer; prompt-change regression and red-team testing; mutation-testing as the correctness metric for generated test cases specifically.
- **Never owns:** a hand-rolled, one-off "LLM as judge" check built inside a single module.
- **Talks to:** wired into CI; every module's prompt/output logic must pass its eval suite before merge.
- **Owned by:** a foundation-layer service, present from each module's first working version.

### LLM Gateway
- **Owns:** the single path through which any module calls a language model; per-module model assignment as configuration; provider abstraction, cost tracking, fallback. **Owns, new:** enforcement of a per-tenant cost ceiling (see Final Engineering Principles).
- **Never owns:** module-specific prompt logic; product decisions ("the gateway decides the risk score").
- **Talks to:** this is a hard rule — no module may call a model provider directly, under any circumstance.
- **Owned by:** a foundation-layer service, decided once.

### Configuration Service
- **Owns:** versioned, tenant-overridable configuration — the risk-to-coverage heuristic, the escalation confidence threshold, the LLM gateway's per-module routing table, and any future value with the same "will be calibrated later" shape.
- **Never owns:** genuine, stable architectural decisions (which entities the graph contains) — not a dumping ground for every constant.
- **Talks to:** read by Modules 2 and 5 and the gateway; changes are versioned, never silent overwrites.
- **Owned by:** a foundation-layer service.

### Authentication
- **Owns:** SSO (SAML/OIDC), directory sync (SCIM), session/tenant handling.
- **Never owns:** module-specific authorization logic — this subsystem establishes *who* someone is, not what they may do.
- **Talks to:** consumed by the API layer for every request, never bypassed.
- **Owned by:** a foundation-layer service; buy-not-build, decided once. **Live configuration staged to first design-partner onboarding — the account/tenant is provisioned in WorkOS at Sprint 0, but full SSO/SCIM setup work happens per-partner, not as a Sprint 0 blocker.**

### Observability
- **Owns:** vendor-neutral instrumentation across every service; LLM-specific tracing; ordinary structured application logging.
- **Never owns:** a substitute for evaluation — observability shows what happened, evaluation judges whether it was correct.
- **Talks to:** every service instruments through the same standard (OpenTelemetry).
- **Owned by:** a foundation-layer service. **Hosting model staged — see Final Technology Stack.**

### Rendering / Reporting Service
- **Owns:** the one transformation from structured, cited entities to a trustworthy human artifact, used today by Release Readiness and the Command Center.
- **Never owns:** module-specific business logic about *what* to render.
- **Talks to:** any future module needing this transformation imports the service, never rebuilds it.
- **Owned by:** shared infrastructure, built once, early.

## 4. Service Architecture

| Service | Purpose | Inputs | Outputs | Consumers | Depends on |
|---|---|---|---|---|---|
| **API Service** | Single externally-reachable surface; tenant/session/auth; routing | Authenticated requests from the frontend | Routed requests; responses and streamed updates | Command Center frontend | Orchestration, graph service, auth |
| **Orchestration Service** | Runs the primary chain and the feedback-loop workflow as one checkpointed, human-gated, crash-tolerant execution | A triggering event (new/updated Requirement; incident action-item extraction) | Sequenced module invocations; persisted intermediate state per step; a fully inspectable completed chain | API service; evaluation subsystem | Connector layer; graph service; LLM gateway |
| **Connector Service** | Ingests events from, and posts status back to, external tools behind one contract | Webhook events; status updates to post back | Normalized internal entities; posted external status | Orchestration service; graph service | Authentication (stored external-tool credentials) |
| **Graph Service** | Read/write API over the Knowledge Layer — schema, temporal state, retrieval | Entity writes from every reasoning module; NL or structured queries | Persisted, versioned entities and relationships; query results with a traceable link to the grounding entity | Every reasoning module; rendering service; Command Center (via API) | None upstream — a foundation-layer producer |
| **LLM Gateway Service** | Sole path from any module to a model provider | A module's structured generation/extraction request, tagged by calling module | The model's response; cost/usage telemetry | Every LLM-driven module, via the structured-extraction backbone | Configuration service (routing table) |
| **Evaluation Service** | Runs regression, retrieval-quality, prompt-change, and mutation-testing checks as CI gates | A module's proposed prompt/logic change plus its eval dataset | Pass/fail gate; a mutation score for Module 3 specifically | CI pipeline, every LLM-driven module | LLM gateway (judge calls); observability (trace-derived examples) |
| **Configuration Service** | Stores and versions the small set of values expected to change with real calibration data | An update to a calibration value | The currently-active, versioned value | Modules 2 and 5; the LLM gateway | Relational store |
| **Rendering Service** | Turns structured, cited entities into a trustworthy human-readable artifact | Entity references plus their citation trail | Rendered artifact (release brief; dashboard view) | Release Readiness module; Command Center | Graph service |

## 5. Data Flow

Unchanged from the Blueprint except at the point marked below.

**Ingestion →** an external tool event (most commonly a Jira ticket) is received by the connector layer, translated into internal shape, and persisted by the graph service as a Requirement entity. Nothing downstream reasons about anything until this happens.

**Requirement reasoning →** the requirement-intelligence module reads the Requirement, produces clarifying questions and draft acceptance criteria, writes back to the same entity. A human reviews and edits before it's treated as validated — nothing auto-commits.

**Risk reasoning →** the risk-and-strategy module reads the validated Requirement plus a derived, graph-resident view of historical defect density, and writes a new Risk Assessment Record — including a stated, human-readable rationale — back to the graph.

**Test design →** the test-design module reads the Requirement and Risk Assessment Record, produces candidate test cases, runs them through the mutation-testing feedback loop, and presents survivors as an editable, reviewable set. Only human-approved cases persist as Test Case entities — discarded generations are never silently kept as if approved.

**Execution →** the connector layer runs the approved suite. Results flow back as Observation/Execution Result entities. This is the durable-execution layer's core scope: a crash here must not corrupt or silently lose an in-flight result, and the module's own test output is never, by itself, treated as proof its own related fix is correct.

**Defect reasoning →** on a failing result, the defect-intelligence module queries the graph for execution history, environment telemetry, and prior similar failures — never the failure log alone — and produces a reproducibility judgment, a defect-vs-flake classification (escalating below a configured confidence threshold), and a business-severity call. Persists as a Defect Report entity, **now including the Waived/Accepted Defect + Rationale attribute where applicable (see Accepted Red Team Changes #1).**

**Release reasoning →** the release-readiness module reads the Risk Assessment Record, accumulated Test Case/Observation results, and open Defect Reports, and produces an aggregated, cited Internal Go/No-Go Document — **now itself carrying the Waived/Accepted Defect + Rationale attribute** — via the shared rendering service. This module never issues the release decision; that boundary is architectural.

**Knowledge query →** a human asks a natural-language question at any point. The answer retrieves specific, relevant entities first and generates a response grounded in, and citing, those entities — never fluent, unattributed prose.

**Feedback and learning →** a production incident is captured (manual entry, or a monitoring integration) as a Production Incident entity. The feedback-loop module extracts action items and updates the affected component's Risk Assessment Record and historical defect-density view. The loop closes concretely the next time a Requirement touches that component.

**Persistence, in one sentence:** anything the data model defines as an entity lives in the graph and nowhere else, scoped by `tenant_id`, under the schema-migration discipline above; anything tenant-, configuration-, or billing-shaped lives in the relational store; anything large and trace-shaped lives in object storage with a retention *and* backup policy; nothing is ever duplicated across two of these three for convenience.

## 6. Interface Philosophy

Unchanged from the Blueprint:

- Every cross-service interaction happens through a contract, not a shared implementation detail.
- Modules communicate through persisted state, never direct calls to each other.
- Shared models (the ten-entity schema) are the single source of truth for what each entity *is*.
- Streaming exists specifically where "watch it happen live" is a real requirement, not as a default.
- Abstractions exist at every boundary with a documented reason to change — never as a general virtue.
- Human-in-the-loop gates are first-class interface points, not UI afterthoughts.
- **New:** schema changes are interface changes. The graph schema is now held to the same "designed before implementation, changed only through a defined process" standard as the connector contract — this is an extension of an existing principle, not a new one.

---

# Final Technology Stack

One decision per row. No alternatives are re-litigated here — the full alternatives-considered reasoning lives in the Engineering Landscape Report and Development Master Plan, and is not repeated. Where this document changes *when* a technology enters the build relative to the Development Master Plan, that is stated explicitly as a staging decision, not a technology change — the eventual technology choice is identical either way.

| Layer | Final Choice | Adoption Point |
|---|---|---|
| **Frontend** | Next.js (App Router) + React, shadcn/ui + Tailwind CSS, TanStack Table/Query, Recharts/visx, WebSocket/SSE | Sprint 0, incremental build against mocked data throughout |
| **Backend** | FastAPI (Python) | Sprint 0 |
| **Relational DB** | PostgreSQL | Sprint 0 |
| **Graph DB** | Neo4j | Sprint 0 — unchanged; **see Overengineering Finding #2 in Rejected Suggestions for why this is not replaced with Postgres** |
| **Temporal fact-versioning** | Graphiti, wrapped on Neo4j | **Staged — not Sprint 0.** V1 ships with Neo4j's native timestamps (`created_at`/`updated_at` on every node) as a lightweight proxy. Graphiti is adopted the first time a real "was this Risk Assessment Record still valid when we released" query is needed by a design partner or by Module 6/7 in earnest — named trigger, not a vague "later" |
| **Vector search** | Neo4j native vector indexes | Sprint 0 for V1 scale; `pgvector`/Qdrant deferred, unchanged |
| **RAG / graph construction** | LightRAG-style construction for V1; Microsoft GraphRAG deferred to Phase 2+ | Sprint 0 (lightweight construction only) |
| **Reranker** | A named cross-encoder reranker, model TBD by Module 7's implementer | **Staged — not Sprint 0.** V1 ships on Neo4j's native hybrid search alone; a reranker is added the first time a real retrieval-precision problem is observed, not preemptively |
| **OCR / document parsing** | Docling (self-hosted default); LlamaParse, Unstructured, PyMuPDF4LLM as documented Phase 2+ options | Out of V1 scope entirely, unchanged |
| **Evaluation** | DeepEval (CI gate) + RAGAS (retrieval) + Promptfoo (regression/red-team) | Sprint 0, wired into CI from each module's first prompt |
| **Mutation testing** | One engine at V1, matching the fixed demo app's language. **Assumption, stated explicitly: the demo app is JavaScript/TypeScript, matching the Command Center stack and Playwright's most common target — Stryker is the V1 engine.** `mutmut`/`cosmic-ray` (Python) and PIT (JVM) remain documented Phase 2+ reference only | Sprint of Module 3's build |
| **Observability instrumentation** | OpenTelemetry | Sprint 0 |
| **LLM tracing** | Self-hosted Langfuse | **Staged.** Internal build/demo work (synthetic demo-app data only) runs on Langfuse Cloud (managed) or plain OpenTelemetry export. Self-hosting is stood up before the first real design-partner ticket or defect flows through the system — not before, because the entire rationale for self-hosting is design-partner data sensitivity, and there is no such data before onboarding |
| **Application logging** | `structlog` + a log-aggregation backend | Sprint 0 |
| **Authentication** | WorkOS (buy) | Sprint 0 for tenant provisioning; **live SSO/SCIM configuration staged to first design-partner onboarding**, per-partner |
| **Durable workflow execution** | Temporal, wrapping Module 4's trigger/collect/gate orchestration | **Staged — later than the Development Master Plan's original "enters at Module 4."** V1's design-partner pilot runs on LangGraph's native checkpointing alone; the self-verification rule (a module's output is never its own sole gate) is enforced as an orchestration state-machine gate that exists regardless of which durability layer sits under it. Temporal is adopted at the first of: (a) the product moves to unattended, always-on production usage, or (b) a live design-partner deployment experiences a crash-related data-loss incident. This is a named trigger, not an indefinite deferral — see ADR-005 |
| **Agent framework** | LangGraph (inner reasoning-chain orchestration); Claude Agent SDK (per-module agent logic); DSPy (prompt optimization for Modules 1, 2, 5); Langfuse Prompt Management (versioned prompt store) | Sprint 0 for LangGraph skeleton; DSPy wrapped in as each of Modules 1/2/5 is built |
| **Structured extraction** | Structured outputs + Instructor/Pydantic AI | Sprint 0, as the shared `packages/extraction` backbone |
| **LLM gateway** | Self-hosted LiteLLM | Sprint 0 |
| **Schema codegen** | Canonical entity/relationship types authored once as Pydantic models in `packages/schemas`; generated into TypeScript via `datamodel-code-generator`/`quicktype` in the same build step | Sprint 0 — **names the previously-unnamed toolchain, closing Moderate Concern #3** |
| **Object storage** | S3-compatible storage (or Cloudflare R2) | Sprint 0, with a flat retention window at V1 (tiering deferred) **and a backup/DR policy defined before first write — closing Major Risk #8 / Underengineering #2** |
| **Deployment** | Standard containerized cloud deployment (or an early-stage PaaS — Fly.io/Render) | Sprint 0. No on-prem inference, no desktop packaging, for V1 — vLLM and Tauri remain the documented Phase 2+ contingency picks, unchanged |
| **Connector adapters (V1)** | Jira Cloud, GitHub, Slack, Playwright — thin adapters behind the connector contract | Sprint of Module 10's build |
| **Connector adapters (legacy/Phase 2+)** | Selenium, Appium, BrowserStack — contract-compatible, not implemented | Deferred until a second real execution target is named. The contract's generality is proven at V1 by a fake adapter in the contract's own test suite, not by shipping unused code |

**Why these staging changes do not weaken the architecture:** every technology in the Development Master Plan's original stack is still the frozen, eventual choice. Nothing was removed from the plan. What changed is that six items (Graphiti, a dedicated reranker, self-hosted Langfuse, Temporal, live SSO/SCIM config, legacy adapters) now have a named adoption trigger instead of defaulting into Sprint 0 by convention. This directly answers the Red Team's Critical Issue #4 (Sprint 0 as a serialized seven-system big-bang) by removing two of those seven systems (Graphiti, Temporal) from Foundation's critical path entirely, without touching the technologies those two systems will still eventually be.

---

# Final Repository Structure

A single monorepo. The connector interface, the graph substrate, and the extraction backbone are visibly shared packages, never code copied into each module. Marked lines are new or changed relative to the Development Master Plan's original structure — every unmarked line is unchanged.

```
qa-os/
├── apps/
│   └── web/                        # Module 9 — Next.js Command Center dashboard
│
├── services/
│   ├── api/                        # FastAPI — external-facing surface, tenant/auth/session, routers
│   ├── orchestrator/                # LangGraph reasoning-chain workers (Modules 1–6, 8)
│   │                                #   + Temporal workers/activities — [STAGED, see Final Technology Stack;
│   │                                #     scaffolded behind a feature flag, not activated at Sprint 0]
│   ├── connectors/                  # Module 10 — one subfolder per external tool adapter
│   │   ├── github/
│   │   ├── jira/
│   │   ├── slack/
│   │   ├── playwright/
│   │   └── legacy/                  # Selenium / Appium / BrowserStack — [DEFERRED: contract-test fake only,
│   │                                #   no real adapter code until a second execution target is named]
│   └── graph-service/               # Module 7 substrate — Neo4j read-write API,
│                                    #   Text-to-Cypher + retrieval endpoint
│                                    #   [NEW] tenant_id enforcement layer — the only code path
│                                    #   permitted to issue a Cypher query
│                                    #   [NEW] schema migration/compatibility-check harness
│
├── packages/                        # shared libraries — imported, never copy-pasted
│   ├── connector-contract/          # the internal Connector interface definition
│   ├── kg-client/                   # typed client for graph-service — [NEW] the sole tenant-scoping
│   │                                #   chokepoint; no other code queries Neo4j directly
│   ├── extraction/                  # structured-output + Instructor/Pydantic AI backbone
│   ├── llm-gateway-client/          # LiteLLM client wrapper, per-module model-config resolver,
│   │                                #   [NEW] per-tenant cost-ceiling enforcement
│   ├── config-service/              # versioned, tenant-overridable configuration objects
│   ├── rendering/                   # shared "structured entities → cited human artifact" service (M6 + M9)
│   ├── schemas/                     # canonical entity/relationship types, single source of truth —
│   │                                #   [NEW] generated into Python (Pydantic, authored) and TypeScript
│   │                                #   (via datamodel-code-generator/quicktype) in the same build step
│   └── ui-components/               # shadcn/ui-based shared component library for apps/web
│
├── modules/                         # AI-reasoning logic proper — one folder per product module,
│   │                                #   each importing from packages/, never reaching into another
│   │                                #   module's internals directly
│   ├── module-01-requirement-intelligence/
│   ├── module-02-risk-strategy/
│   ├── module-03-test-generation/
│   ├── module-04-execution-orchestration/
│   ├── module-05-defect-triage/
│   ├── module-06-release-readiness/
│   ├── module-08-feedback-learning-loop/
│   └── module-99-environment-data-strategy/     # DELIBERATELY EMPTY — Phase 2+ placeholder, no code
│
├── prompts/                         # every module's versioned prompts, one folder per module,
│   │                                #   each prompt paired with its eval dataset (never separated)
│   ├── module-01/
│   ├── module-02/
│   └── ...
│
├── evals/                           # DeepEval / RAGAS / Promptfoo suites, mirroring modules/
│   ├── module-01/
│   ├── module-02/
│   └── ...
│
├── mutation-testing/                # [CHANGED] Stryker config only at V1 (demo app is JS/TS);
│                                    #   mutmut/cosmic-ray/PIT configs documented, not wired into CI,
│                                    #   until a real codebase in that language exists
│
├── infra/
│   ├── neo4j/                       # graph DB provisioning; [NEW] tenant_id migration/backfill scripts;
│                                    #   [NEW] backup/DR job definitions; Graphiti migration scripts
│                                    #   staged for the Graphiti adoption trigger, not run at Sprint 0
│   ├── postgres/                    # relational schema migrations
│   ├── temporal/                    # workflow/activity deployment config — [STAGED] provisioned but
│                                    #   not deployed until the Temporal adoption trigger fires
│   ├── litellm/                     # gateway config, per-module routing table,
│                                    #   [NEW] per-tenant budget-cap definitions
│   ├── langfuse/                    # [STAGED] self-hosted deployment config, deployed at the
│                                    #   self-hosting adoption trigger; managed Langfuse Cloud config
│                                    #   used until then
│   ├── auth/                        # WorkOS configuration — tenant provisioning at Sprint 0;
│                                    #   [STAGED] per-partner SSO/SCIM setup scripts, run at onboarding
│   └── deploy/                      # containerized cloud deployment manifests
│
└── docs/
    └── adr/                         # [NEW] Architecture Decision Records — ADR-001 through ADR-012,
                                     #   this document's ADR section, version-controlled alongside code
```

**Foundation fallback, named explicitly (closes Critical Issue #4):** `packages/kg-client` and the auth check in `services/api` each ship with a stub/fake implementation from day one of Sprint 0, swappable via configuration for the real Neo4j and WorkOS backends. If graph or auth provisioning runs long, Module 1 development starts against the stub and swaps to the real backend when it lands — Foundation's critical path no longer serially blocks every downstream module on every one of its seven components landing simultaneously.

---

# Final Module Definitions

Every module's responsibilities, inputs, outputs, dependencies, and ownership. Demo-quality Definition of Done is carried forward from the Development Master Plan unchanged except where a fix below alters it (marked). Full task/sprint-level breakdown is Phase 2 scope, not redefined here.

### Module 1 — Requirement Intelligence
- **Responsibilities:** ingest a Requirement; identify implicit gaps against a versioned, evidence-based ambiguity/gap taxonomy (not generic completeness rules); draft clarifying questions and acceptance criteria.
- **Inputs:** a Requirement entity from the connector layer.
- **Outputs:** clarifying questions and draft acceptance criteria, written back to the Requirement entity; human review required before validation.
- **Dependencies:** `kg-client`, `extraction`, LLM gateway, evaluation harness, DSPy.
- **Ownership:** Module 1 team. Foundational — everything downstream depends on it.
- **Definition of Done (unchanged):** given one realistic Jira ticket, produces clarifying questions and draft acceptance criteria from a visibly-fired checklist item, presented as an editable, reviewable artifact.

### Module 2 — Risk & Test Strategy Engine
- **Responsibilities:** assess change risk (Change Surface, Historical Defect Density, Business Criticality); compute Risk Exposure Score; recommend coverage depth with a stated rationale.
- **Inputs:** a validated Requirement; a repo diff; graph-resident historical defect density.
- **Outputs:** a Risk Assessment Record, including Stated Rationale, written to the graph.
- **Dependencies:** `kg-client`, `config-service` (risk-to-coverage heuristic), LLM gateway, DSPy.
- **Ownership:** Module 2 team.
- **Definition of Done (unchanged):** produces a Risk Assessment Record plus one sentence of rationale citing an actual graph-sourced number; the heuristic is swappable via config without a redeploy. **Still the single largest live credibility risk in the product** — the coverage-depth conversion remains provisional, calibrated jointly with each design partner's QA lead per Accepted Change #6.

### Module 3 — Test Design & Case Generation
- **Responsibilities:** generate functional/boundary/negative test cases; run the generate→mutate→discard→review loop; present survivors for mandatory human review.
- **Inputs:** the Requirement and Risk Assessment Record.
- **Outputs:** human-approved Test Case entities only; discarded generations are never silently retained as approved.
- **Dependencies:** `extraction`, mutation-testing engine (Stryker at V1), evaluation harness.
- **Ownership:** Module 3 team.
- **Definition of Done (unchanged):** generates test cases, runs at least one mutation-testing pass, presents survivors in a reviewable, editable UI. No auto-commit path exists.

### Module 4 — Execution Orchestration Layer
- **Responsibilities:** trigger the approved suite via the connector layer; collect Observation/Execution Result entities; enforce the hard rule that a module's own test result is never the sole gate on its own related fix.
- **Inputs:** an approved Test Case set.
- **Outputs:** Observation/Execution Result entities and trace artifacts.
- **Dependencies:** connector layer (Playwright adapter), object storage, orchestration layer.
- **Ownership:** Module 4 team.
- **Definition of Done (unchanged):** the approved suite runs live against the fixed demo app with progress streamed to the dashboard; the self-verification firewall is demonstrably in place. **Durable-execution requirement staged per Final Technology Stack** — the self-verification gate is enforced in the orchestration state machine regardless of whether Temporal is deployed yet.

### Module 5 — Defect Intelligence & Triage
- **Responsibilities:** on a failing result, query graph context (execution history, environment telemetry, prior similar failures — never logs alone); produce a reproducibility judgment, a defect-vs-flake classification with a calibrated confidence score (escalating below threshold), and a business-severity call.
- **Inputs:** a failing Observation/Execution Result.
- **Outputs:** a Defect Report entity, **including the Waived/Accepted Defect + Rationale attribute where a defect is triaged as accepted risk rather than blocking (Accepted Change #1).**
- **Dependencies:** `kg-client`, `config-service` (escalation threshold), LLM gateway.
- **Ownership:** Module 5 team. Gated on Module 7's retrieval quality, not independent ML work — no standalone flaky/defect classifier is built.
- **Definition of Done (unchanged, plus the new attribute).**

### Module 6 — Release Readiness & Go/No-Go Advisor
- **Responsibilities:** aggregate the Risk Assessment Record, coverage results, and open Defect Reports into a cited Internal Go/No-Go Document; advisory only, never an autonomous release trigger.
- **Inputs:** Risk Assessment Record, Test Case/Observation results, Defect Reports.
- **Outputs:** an Internal Go/No-Go Document, **now carrying the Waived/Accepted Defect + Rationale attribute directly (Accepted Change #1)**, rendered via the shared rendering service, posted to GitHub as an advisory Check Run.
- **Dependencies:** `rendering`, `kg-client`.
- **Ownership:** Module 6 team. Least open research risk of the ten — templated aggregation.
- **Definition of Done (changed):** as before, plus the go/no-go brief must visibly surface any waived-defect rationale it aggregates — this is now a completion-criteria requirement, not an incidental side effect of the schema change.

### Module 7 — Organizational QA Knowledge Graph
- **Substrate responsibilities (foundation-layer, built first):** the ten-entity schema and relationships; read/write APIs; **tenant isolation enforcement; schema migration discipline** (both new, see Final Architecture §3).
- **Product-surface responsibilities (built last among reasoning modules):** natural-language query, answering with a citation to the specific grounding entity, never unattributed prose.
- **Inputs (substrate):** every reasoning module's entity writes. **Inputs (surface):** a natural-language question.
- **Outputs (substrate):** persisted, versioned, tenant-scoped entities. **Outputs (surface):** a cited answer referencing specific entity IDs.
- **Dependencies:** Neo4j, `kg-client`, LightRAG-style construction, Text-to-Cypher.
- **Ownership:** the substrate is a foundation-layer service; the product surface is the Module 7 team's late-stage deliverable.
- **Definition of Done:** substrate — the schema is live, Modules 1 and 2 read/write against it without a schema change, tenant scoping is enforced by `kg-client` before any second tenant's data is written. Surface — a natural-language query matching the demo script returns a cited answer.

### Module 8 — Production Feedback & Incident Learning Loop
- **Responsibilities:** capture a Production Incident (manual entry or monitoring integration); extract action items; update the affected component's Risk Assessment Record and Historical Failure Pattern-lite counter. Deliberately narrow — no auto-generation of new test cases or ADRs from an incident at V1.
- **Inputs:** a Production Incident entity.
- **Outputs:** updated Risk Assessment Record and Historical Failure Pattern-lite entity.
- **Dependencies:** `extraction` (reused from Module 1), `kg-client` (reused write path from Module 7).
- **Ownership:** Module 8 team. Built last among reasoning modules, deliberately.
- **Definition of Done (unchanged), with one process addition (Accepted Change #9):** the module's core "AI-Augmented" capability classification undergoes a validation spike before this module's sprint starts — not assumed correct because the tooling to build it exists.

### Module 9 — QA Command Center
- **Responsibilities:** role-aware dashboard (minimum: QA Engineer view, QA Lead view) live-streaming the full primary chain as one coherent, persisted history; per-module trust/reliability indicators shown separately, never blended into one confidence number.
- **Inputs:** the full reasoning chain's live and historical state, via the API layer.
- **Outputs:** a rendered, role-aware view; forwarded human-review actions.
- **Dependencies:** `rendering`, `ui-components`, API service, streaming channel.
- **Ownership:** Module 9 team. Built incrementally in parallel with every other module, hardened as a final integration pass.
- **Definition of Done (unchanged).**

### Module 10 — Integration & Extensibility Layer
- **Responsibilities:** the internal connector contract; thin adapters for Jira Cloud, GitHub, Slack, Playwright at V1.
- **Inputs:** webhook events from external tools.
- **Outputs:** normalized internal entities; posted external status updates.
- **Dependencies:** authentication (external-tool credentials).
- **Ownership:** Module 10 team. Built first among the ten modules — the literal front door.
- **Definition of Done (unchanged):** all four V1 adapters demo-ready; legacy adapters present behind the contract only, not demo-ready — **now explicit that "present behind the contract" means a contract-test fake, not real adapter code (Accepted Change, Demo Optimization #4).**

### Environment / Data Strategy (Module 99 — placeholder only)
- **Status:** Phase 2+, not built, no entities in the V1 schema. Explicitly disclosed to design partners as a sequencing choice, not a blind spot, per the Master Specification's own resolution of this exact flagged mismatch.

---

# Shared Infrastructure

Built once, by no single module team, consumed by many. Each earns shared status because more than one module needs it in materially the same shape.

| Shared component | What it is | Consumed by | Status |
|---|---|---|---|
| **Connector interface** | One `Connector` contract (auth, event-subscribe, artifact-fetch, status-post), with thin adapters per tool | Module 10 owns it; Modules 1, 4, 6 consume directly | Frozen, unchanged |
| **Knowledge Graph substrate** | Neo4j; the ten-entity schema; **tenant_id scoping enforced solely in `kg-client`; additive-only migration discipline with a compatibility-check gate** | Modules 1, 2, 5, 6, 7, 8 | **Frozen with two new properties (isolation, migration discipline) — closes Critical Issues #2 and #3** |
| **Structured-extraction backbone** | Structured outputs + Instructor/Pydantic AI | Modules 1, 6, 8 | Frozen, unchanged |
| **LLM gateway** | Self-hosted LiteLLM, per-module model assignment as config, **per-tenant budget ceiling with a defined mid-chain-exhaustion behavior** | Every LLM-driven module | **Frozen with one new property (cost governance) — closes Major Risk #9 / Underengineering #1** |
| **Reasoning-chain orchestrator** | LangGraph (checkpointed) at V1; Temporal (durable) staged to a named trigger | Modules 1–6, 8 | **Frozen with an explicit staged-adoption trigger — closes Overengineering #1 and Critical #4 in part** |
| **Prompt framework** | DSPy (rubric-scored extraction optimization) + versioned prompt store | Modules 1, 2, 5 primarily | Frozen, unchanged |
| **Evaluation harness** | DeepEval + RAGAS + Promptfoo + mutation-testing (Stryker at V1) | Every LLM-driven module, from its first sprint | Frozen; **includes an explicit synthetic-to-real-data eval switchover criterion (Accepted Change #7)** |
| **Observability** | OpenTelemetry + Langfuse (managed during internal build, self-hosted before real design-partner data flows) | Every service | **Frozen with a staged hosting model — closes Demo Optimization #2 without abandoning the original data-sensitivity rationale** |
| **Authentication** | WorkOS (SSO, SCIM, audit logs); tenant provisioned Sprint 0, live SSO/SCIM configured per design partner | The whole product | Frozen; timing staged |
| **Configuration service** | Versioned, tenant-overridable config; **now paired with a minimum calibration-process definition** | Modules 2, 5; the gateway | **Frozen with a new process requirement — closes Major Risk #3 / Underengineering #6** |
| **Shared rendering/citation service** | One "structured entities → cited human artifact" service | Modules 6 and 9 | Frozen, unchanged |
| **Object storage** | S3-compatible, **flat retention window plus a mandatory backup/DR policy from first write** | Module 4's trace archives primarily | **Frozen with a new DR requirement — closes Major Risk #8 / Underengineering #2** |
| **Design system** | shadcn/ui + Tailwind component library | Module 9, any future admin surface | Frozen, unchanged |
| **Schema codegen toolchain** | Pydantic-authored canonical types, generated to TypeScript via `datamodel-code-generator`/`quicktype` | `packages/schemas` consumers (API, web, all modules) | **New — closes Moderate Concern #3** |
| **On-call ownership model** | Foundation-layer services (API, orchestrator, graph service, connector layer, storage, config service, observability) are owned by a named rotating Platform pod with a real pager, not diffusely "collectively owned" | All seven foundation-layer services | **New — closes Major Risk #5 / Underengineering #4** |
| **Indirect prompt-injection guardrail** | A threat model and a Promptfoo red-team suite specifically for the ingestion→action path (ticket/PR text driving Slack messages, Check Runs, generated test content) | Modules 1, 4, 6, 10 | **New — closes Underengineering #3 / Moderate Concern #5; the specific threat model is a Sprint 0 deliverable, not deferred — see Deferred Decisions for what remains Phase 2** |

---

# Final Engineering Principles

The permanent engineering constitution. Items 1–18 are carried forward unchanged from the Implementation Blueprint and Development Master Plan (numbering consolidated, duplicates merged). Items 19–24 are new, added by this document to close Red Team findings. None of these is a suggestion or a team-level judgment call — each is either a direct architectural decision or a direct consequence of one.

1. **No module calls an LLM provider directly, ever.** Every model call goes through the LLM gateway and the shared structured-extraction backbone.
2. **No module stands up a second memory or retrieval system.** The Knowledge Graph is the system's institutional memory, full stop.
3. **No module duplicates the structured-extraction primitive.** A module needing structured output imports `packages/extraction`; it does not write its own parse-and-retry loop.
4. **Values expected to be calibrated later are configuration from the day they first appear, never hard-coded.** Applies without exception to the risk-to-coverage heuristic, the defect/flake escalation threshold, and per-module model routing.
5. **The connector interface is designed before the first tool-specific integration is written**, and no connector — present or future — is added except behind that same contract.
6. **No module reaches into another module's internals.** Cross-module communication happens through shared packages, persisted graph state, or the orchestrator — never a direct import between `modules/module-0X/` folders.
7. **A module's own generated output is never the sole gate on its own verification.** Applies today to Module 4's execution results and to any future module where an AI system could be positioned to grade its own work.
8. **Every LLM-driven module ships with an attached evaluation dataset from its first working version**, and no prompt change merges without that evaluation suite passing.
9. **Auto-generated artifacts are tagged distinctly from human-authored ones in the data model**, starting with Module 3's generated tests — never silently mixed into the historical signal Module 2 depends on.
10. **Every module is independently testable against the shared evaluation harness**, not validated only by the end-to-end demo script passing once.
11. **Object storage retention policy — and, as of this document, backup/DR policy — is set on the first artifact write**, not after storage cost or data loss becomes a live incident.
12. **The rendering/citation service is shared, never rebuilt per module.**
13. **The Knowledge Graph is the system's source of truth for every entity the data model defines.** No entity is shadow-copied into the relational store for convenience.
14. **Release go/no-go is always advisory, never an autonomous trigger.** Hard product and architectural constraint, not configurable behavior.
15. **Human review is retained wherever the architecture names it as mandatory** (test-case approval, release decisions) — no auto-commit path exists around these gates, regardless of model confidence.
16. **Frozen scope stays frozen.** Environment/Data Strategy and the richer production-feedback-to-ADR/test-case mechanism are Phase 2+ by explicit, cited decision — the fact that the tooling to build them now exists is not authorization to build them now.
17. **Structured outputs, not free-form generation, are the contract between a module and the rest of the system**, wherever a module's output is consumed downstream or persisted as an entity.
18. **Prompts are versioned, never edited in place without a version boundary.**
19. **[NEW] The graph schema is designed before the first entity write, changed only additively, and every change ships with a compatibility check against every consuming module's read path.** This is the connector-contract discipline, applied to the second-highest-blast-radius surface in the system.
20. **[NEW] `kg-client` is the only code path in the system permitted to issue a graph database query. Every query filters on `tenant_id`.** No exceptions for "internal tooling" or "just this once" scripts.
21. **[NEW] Any infrastructure component with a staged adoption trigger (Temporal, Graphiti, self-hosted Langfuse, a dedicated reranker, live SSO/SCIM configuration) has that trigger written down before Sprint 0, not decided informally when the moment arrives.** The triggers themselves are frozen in the Final Technology Stack table above; only their firing is deferred.
22. **[NEW] Foundation-layer services have a named on-call owner, not a diffuse "collectively owned" label.** "Collectively owned" describes who may contribute code; it does not answer who is paged.
23. **[NEW] Every tenant has a defined per-tenant LLM cost ceiling in the gateway, with a defined behavior when it's hit mid-chain (the in-flight step fails closed and surfaces a human-visible error — it does not silently degrade to a cheaper model or silently drop the request) and a defined alert owner.**
24. **[NEW] No LLM-generated synthetic evaluation or training data is treated as a permanent substitute for real design-partner-derived data.** Synthetic data is a documented, acceptable Sprint 0–era stopgap; each module's eval suite and DSPy optimization set must define, at build time, the specific real-data threshold (a stated minimum sample count from real tickets/defects) at which synthetic data is phased out — this is a completion criterion for "V1-core, calibrated," not an indefinite steady state.

---

# Accepted Red Team Changes

Every accepted finding, what changed, and why. Numbered independently of the Red Team's own numbering (which mixed Critical Issues, Major Risks, Underengineering, Moderate Concerns, Minor Improvements, and Demo Optimizations into separate lists) so this ledger reads as one coherent set of decisions.

| # | Red Team Finding | Source | What Changed | Why |
|---|---|---|---|---|
| **1** | Waived/Accepted Defect + Rationale attribute missing from Internal Go/No-Go Document and Defect Report | Critical Issue #1 | The attribute is added to both entities in the Sprint 0 schema, under the new schema-migration discipline (Principle #19) | This was the pipeline's own "single most material finding." The product's headline differentiator against standard release notes *is* this mechanism; shipping Sprint 0 without it would mean building Modules 5 and 6 against a shape that has to be migrated later, under live design-partner data, on the exact entity the sales narrative depends on. A trivial schema addition today is a live-data migration in three sprints. |
| **2** | No multi-tenancy isolation strategy for the Knowledge Graph | Critical Issue #2 | Isolation model decided: shared Neo4j instance, mandatory `tenant_id` on every node/relationship, enforced solely in `kg-client` (Principle #20). Physical per-tenant separation deferred as a Phase 2+ upgrade path | Auth got a "buy once, early, never revisit" decision precisely because retrofitting auth under a live enterprise customer is a named failure mode. The identical logic applies to tenant isolation in the one store holding the most sensitive data in the product, and it had received zero design treatment across six documents. |
| **3** | No graph schema migration/versioning discipline | Critical Issue #3 | Additive-only schema changes, an explicit deprecation window for removals, and a mandatory compatibility check against every consuming module's read path before a schema change merges (Principle #19) | The connector contract has exactly this discipline; the graph — read or written by six of ten modules, the single most shared and most mutated piece of state in the system — did not. Finding #1 above is a live example of a schema change this project already knows it needs; this principle is what prevents the next one from becoming an unplanned migration. |
| **4** | Sprint 0 is a serialized big-bang across ~7 unfamiliar systems | Critical Issue #4 | (a) Graphiti and Temporal removed from Foundation's critical path entirely (staged to later triggers, Final Technology Stack); (b) `kg-client` and the auth check ship with a stub/fake from day one, swappable to the real backend, so Module 1 can start even if Neo4j or WorkOS provisioning runs long | Foundation gated the entire ten-module sequence on all seven of its components landing simultaneously, with no fallback if any one ran long — and the report itself notes at least one component running long is likely given the field's own quarters-not-years pace of change. Removing two components from the critical path and adding a stub-and-swap fallback for the remaining ones converts a single point of schedule failure into a manageable one. |
| **5** | Aggregate integration tax across ~15 third-party systems never summed | Major Risk #1 | No architecture change. Added as a standing risk-register entry with an explicit onboarding runbook requirement: any new engineer's first week includes a written map of which of the ~15 systems they'll touch and in what order, rather than all fifteen being assumed background knowledge | This is a real, named risk, but it is a staffing/onboarding mitigation, not an architecture decision — the individual technology choices remain each well-justified on their own terms, and undoing any one of them to reduce the count would be a worse trade than managing the onboarding cost directly. |
| **6** | "Calibrate during pilot" has no described mechanism for Module 2's heuristic or Module 5's threshold | Major Risk #3 | The Configuration Service now requires, before either value exits "provisional": a named calibration-session owner (the Module 2/5 team lead, jointly with the design partner's QA lead), a stated minimum sample size before a value is called calibrated rather than "still guessing," and a documented tie-breaking rule for disagreement between two design partners' QA leads (defer to the partner whose domain most closely matches the component being assessed; log the disagreement itself as a data point) | "Will be calibrated during pilot" was a sentence, not a process, on the single-biggest-credibility-risk value in the entire product by the documents' own repeated admission. This does not supply the calibrated *values* — those remain genuinely unknowable before real usage — it supplies the process that will produce them, which is what was actually missing. |
| **7** | DSPy and the eval harness both need labeled data that doesn't exist pre-launch; nothing says when synthetic data gets replaced | Major Risk #2 | Principle #24 added: every module's eval suite defines, at build time, the specific real-data sample-count threshold at which synthetic data is phased out | Using an LLM to generate the eval data that grades an LLM-generated system is a reasonable, well-established stopgap — the gap was that nothing said when the stopgap ends. This closes that gap without touching the technique itself. |
| **8** | No on-call/ownership model for seven "collectively owned" foundation services | Major Risk #5 / Underengineering #4 | A named, rotating Platform pod now owns the on-call pager for all seven foundation-layer services (Principle #22) | "Collectively owned" answers who may contribute code. It does not answer whose pager fires at 2am when the graph service has an incident. Diffusely-owned, highest-blast-radius infrastructure is a well-known rot pattern, and naming a rotation is a near-zero-cost fix relative to the risk it closes. |
| **9** | Module 8's core AI-Augmented classification was never validated, and it's fully scheduled anyway | Major Risk #6 / Underengineering #5 | A validation spike is added as a required checkpoint before Module 8's sprint starts, with an explicit possible outcome ("this needs to be Human-Only, not AI-Augmented") that is a scope conversation, not a mid-sprint surprise | Module 8 is deliberately the pipeline's thinnest-evidence module already; scheduling it as a normal build item with no validation gate risks discovering a scope problem mid-build rather than before it, which is exactly the kind of throwaway work this plan is otherwise designed to avoid. |
| **10** | No backup/disaster-recovery policy for the Knowledge Graph | Major Risk #8 / Underengineering #2 | A backup/DR policy is now a Sprint 0 deliverable alongside the retention policy, both attached to object storage and to the graph substrate before first write (Principle #11) | The product's entire differentiator is that judgment compounds with usage. Losing the graph without a recovery path isn't a bad day operationally — it's losing the product's only real moat. This received zero mentions across six documents and is now a named Sprint 0 requirement. |
| **11** | No per-tenant cost governance policy for LLM spend, only a cited capability | Major Risk #9 / Underengineering #1 | A per-tenant budget ceiling, a defined fail-closed behavior on mid-chain exhaustion, and a named alert owner are now required gateway configuration (Principle #23) | LiteLLM's virtual-key and budget-cap *capability* was cited as if it were a *policy*. A capability without a ceiling, a failure behavior, and an owner is not governance — it's an unexercised feature. |
| **12** | No indirect-prompt-injection threat model for ingested ticket/PR content | Underengineering #3 / Moderate Concern #5 | A specific threat model for the ingestion→action path (Module 1 ingesting ticket text that ultimately drives Slack messages, GitHub Check Runs, and generated test content) plus a Promptfoo red-team suite targeting exactly that path are added as a Sprint 0 deliverable | Promptfoo's general red-teaming capability was named; a threat model for this system's specific, plausible injection vector was not. A crafted or compromised ticket driving downstream external-system actions is a concrete, nameable risk given the architecture's own design, not a hypothetical one. |
| **13** | No named codegen toolchain for the cross-language schema package | Moderate Concern #3 | `packages/schemas` is now specified as Pydantic-authored, generated to TypeScript via `datamodel-code-generator`/`quicktype` in the same build step | Every other technology decision in this stack names a specific tool and a specific rejected alternative; this one didn't, despite being foundational to keeping the FastAPI backend and Next.js frontend from drifting apart. |
| **14** | Repository structure doesn't uniformly match the "ten uniform modules" framing (Modules 7, 9, 10 are full services; the rest are folders) | Moderate Concern #6 | No structural change — the pragmatic split is correct and is kept. The mismatch is now named explicitly in this document (Final Repository Structure) rather than left as an implicit inconsistency between what the documents say and what the folder tree shows | The Red Team's own framing: this is worth naming, not fixing. A uniform-module folder structure would be worse engineering than the pragmatic one already chosen; the fix is honest documentation, not a restructure. |
| **15** | Jira custom-field variance budgeted inconsistently (Sprint 0 line item in some places, ongoing cost in others) | Moderate Concern #7 | Explicitly reclassified here as a recurring, per-design-partner-onboarding cost, to be budgeted in every partner-onboarding sprint, not only Sprint 0 | The Landscape Report was already honest that this recurs; this document makes sure that honesty shows up in how sprints are actually planned, not just in a risk-register bullet. |
| **16 (Demo Optimization)** | Dual orchestration frameworks (LangGraph + Temporal) adopted simultaneously for a scripted demo | Overengineering #1 / Demo Optimization #1 | Temporal staged to a named later trigger — see Final Technology Stack and Principle #21 | Real, unresolved reliability engineering bought before there's a workload that needs it unattended. The self-verification rule itself is preserved unconditionally (Principle #7) via an orchestration state-machine gate; only the durable-execution *implementation* under that gate is staged. |
| **17 (Demo Optimization)** | Self-hosted Langfuse from day one, before any design-partner data exists | Demo Optimization #2 | Staged: managed Langfuse Cloud (or plain OpenTelemetry export) during internal build against the fixed demo app's synthetic data; self-hosted before the first real design-partner ticket or defect flows through the system | Partially accepted, not fully: the original rationale (design-partner data sensitivity) is preserved exactly, because it applies at first real design-partner use, not at "first paying customer" as the Red Team's Demo Optimization framing suggested. The staging trigger is moved earlier than the Red Team proposed, specifically to keep that rationale intact. |
| **18 (Demo Optimization)** | WorkOS SSO/SCIM configuration doesn't need to be live in Sprint 0 | Demo Optimization #3 | Buy decision unchanged; live configuration staged to first design-partner onboarding, freeing Sprint 0's critical path | The buy decision was never in question; only the timing of the configuration labor was blocking Sprint 0 unnecessarily. |
| **19 (Demo Optimization)** | Legacy connector adapters (Selenium, Appium, BrowserStack) built and stubbed before a second execution target exists | Overengineering #4 / Demo Optimization #4 | Zero real adapter code until a second execution target is named; the contract's generality is proven via a fake adapter in the contract's own test suite | A single implementation (Playwright) cannot prove an abstraction generalizes. Shipping unused adapter code validates that it compiles, nothing more. |
| **20 (Demo Optimization)** | Four mutation-testing engines configured for a V1 with one demo app in one language | Overengineering #3 / Demo Optimization #5 | Stryker only at V1 (demo app assumed JS/TS — stated explicitly as an assumption); `mutmut`/`cosmic-ray`/PIT remain documented, not CI-wired, until a real codebase in that language exists | The other three engines validate nothing before a real design-partner codebase in that language shows up. |
| **21 (Demo Optimization)** | Graphiti's temporal-fact-versioning layer, distinct from Neo4j itself, bundled into Sprint 0 for a graph explicitly described as "thin at V1" | Demo Optimization #6 | Graphiti staged to a named later trigger (Final Technology Stack); Neo4j itself, and the ten-entity schema, ship unchanged at Sprint 0 | Accepted narrowly: the temporal-versioning *layer* is staged, not the graph database itself. This is distinct from — and does not concede — Overengineering Finding #2's broader proposal to replace Neo4j with Postgres, which is rejected below. |
| **22 (Demo Optimization)** | A dedicated reranker model bundled in for V1's thin corpus | Demo Optimization #8 | Staged to the first real observed retrieval-precision problem; V1 ships on Neo4j's native hybrid search alone | No evidence yet that V1's deliberately thin corpus needs cross-encoder reranking; adding it preemptively is complexity bought against a problem that hasn't been observed. |
| **23 (Demo Optimization)** | Sophisticated object-storage retention tiering from day one | Demo Optimization #7 | A flat retention window at V1; tiering deferred until real storage-cost pressure is observed — **the backup/DR policy is not deferred, and is a separate concern from tiering (see Accepted Change #10)** | Tiering optimizes cost against a bill that doesn't exist yet at design-partner scale; DR protects against data loss, which is a real risk from the first write regardless of scale. The two were conflated in the source review's framing and are separated here. |
| **24** | Add a lightweight ADR for the Module 7 substrate/product-surface split | Minor Improvement #4 | Done — see ADR-011 | The Red Team correctly called this the single best sequencing decision in the plan; it now has a permanent decision record rather than living only as prose in a planning document. |
| **25** | Define numerically what "low confidence" means for Module 5's escalation threshold, even as a placeholder | Minor Improvement #3 | The Configuration Service's schema for this value now requires a placeholder default (documented as provisional, not calibrated) to exist from the value's first appearance, so the first implementer isn't guessing at the shape of the config object | Closes a genuine small gap at near-zero cost — the placeholder is explicitly not a claim that the value is validated. |
| **26** | Module 9's "per-module trust indicators, never blended into one number" needs a small explicit UI spec now | Minor Improvement #5 | Flagged as a Phase 2 requirement with elevated priority — a small, explicit indicator-model spec is now named as a prerequisite for Module 9's first sprint, not left to be improvised per-module as each module lands | Correctly identified as easy to retrofit badly if each module invents its own indicator shape independently. |
| **27** | Name a specific reranker model/library rather than "reranking models" generically | Minor Improvement #1 | Not resolved here — deliberately left to whoever implements the reranker at its staged adoption trigger (Accepted Change #22), since naming a specific model now, before the retrieval-precision problem that justifies adding a reranker at all has even been observed, would be picking a tool for a problem that doesn't yet exist | Logged as accepted-in-principle, resolved-at-adoption-time — see Deferred Decisions. |
| **28** | Specify whether `Historical Failure Pattern (lite)` is computed eager (on write) or lazy (on read) | Minor Improvement #2 | Not resolved here — this is a Module 2 implementation detail below this document's level of resolution (literal schema/query design is Phase 2 scope) — flagged explicitly as a required Module 2 sprint-planning input | Affects Module 2's latency budget concretely enough to matter, but deciding it now, without the concrete query patterns Phase 2's schema work will produce, risks guessing wrong. |

---

# Rejected Red Team Suggestions

| # | Suggestion | Source | Why Rejected |
|---|---|---|---|
| **1** | Replace Neo4j + Graphiti + LightRAG + reranker + Text-to-Cypher with relational tables in Postgres (`valid_from`/`valid_to` columns as a poor-man's temporal layer), migrating to a graph database later once real multi-hop/temporal query patterns are observed | Overengineering Finding #2 | The Red Team's own words: "this is a defensible bet either way... it is a bet made well before the evidence that would justify it exists, and it's worth naming as a bet, not a foregone conclusion." That is explicitly not a critical engineering justification — it's an acknowledged coin-flip presented as an alternative, not a documented flaw in the current choice. This document's mandate is not to replace a major technology on a bet. The graph database itself, and the ten-entity schema's relationship structure, are frozen from the Master Specification and Blueprint; Modules 5 and 7 specifically depend on multi-hop traversal (prior similar failures, execution history, environment telemetry) that a relational poor-man's substitute would have to re-implement as application-level joins, which is a worse position to migrate *from* later than a purpose-built graph is to migrate *within*. Graphiti's temporal layer specifically **is** staged out of Sprint 0 (Accepted Change #21) — that is the part of this finding with real, non-bet reasoning behind it (V1's graph is genuinely thin, and Neo4j's native timestamps are a genuine lightweight proxy for the temporal need specifically). The database engine underneath is not. |
| **2** | Defer Temporal until "a real, live, multi-tenant workload actually needs unattended crash recovery a human isn't watching" — read as a trigger potentially well past first design-partner usage | Demo Optimization #1 (broadest reading) | Partially rejected, partially accepted (see Accepted Change #16). Accepted: Temporal doesn't need to be in Sprint 0. Rejected: an indefinitely vague trigger ("a human isn't watching") is itself the kind of underspecified staging this document exists to close. The trigger is instead pinned to two concrete, checkable conditions (unattended production usage begins, or a crash-related data-loss incident occurs in a live design-partner deployment) — deliberately more specific than the Red Team's own phrasing, so "when do we actually adopt this" isn't left to a future team's judgment call under schedule pressure. |
| **3** | Treat the buy-WorkOS decision itself as revisitable, on the logic that Auth0 or Clerk might be reconsidered once enterprise security review starts | Not a direct Red Team recommendation, but adjacent language in Moderate Concern #4 about security-review readiness could be read this way | Rejected as a misreading worth foreclosing explicitly: the Development Master Plan's WorkOS decision was described as "a genuine research-grounded pick, not a default," with Auth0 and Clerk both explicitly evaluated and rejected on stated criteria. Moderate Concern #4 is about data-residency and audit-log depth *beyond* WorkOS's baseline — a real, accepted gap (see Deferred Decisions) — not about the vendor choice itself. The buy decision is unchanged and not reopened by this document. |

Nothing else in the Red Team review is rejected outright. Every remaining finding is either accepted (above) or genuinely deferred (below) — the review's Executive Summary and "Things We Should NOT Change" section were themselves treated as binding on this document, and every item in that section (config-over-code, the connector interface, the Module 7 substrate/surface split, the self-verification rule, advisory-only release gating, mandatory human review on test generation, buying auth, provenance tagging, static model routing) is preserved unmodified throughout this freeze.

---

# Deferred Decisions

Everything intentionally postponed, and why postponing it now (rather than deciding it in this document) is the correct call — not a gap in this document's authority, but a genuine Phase 2 or later dependency.

| Deferred item | Why it's deferred, not decided here |
|---|---|
| **Concrete API contracts** (endpoints, request/response shapes) for every service in Final Module Definitions/Service Architecture | Requires the literal schema work below it; deciding contract shape before the schema it serializes is settled would risk contract churn the moment the schema work happens. Phase 2 scope, per the Blueprint's own boundary, unchanged. |
| **Literal database schema** — relational tables and graph entity/relationship property definitions implementing the data model this document assumes (including the new Waived/Accepted Defect + Rationale attribute's exact type and the `tenant_id` property's exact enforcement mechanics in Cypher) | This document specifies *that* the attribute and the tenant property exist and *how* they must be enforced structurally (via `kg-client`); it deliberately does not write the literal schema, which is Phase 2's first concrete task under the migration discipline this document establishes. |
| **Repository's literal folder structure below the package level** (internal module file layout, testing conventions) | This document freezes the repository's shape at the package/service boundary; internal-to-package organization is an implementation choice within an already-bounded unit. |
| **Task- and sprint-level breakdown**, including the exact Sprint 0 timebox duration for the Foundation fallback (Accepted Change #4) | Requires real team-capacity input this document does not have. The *fallback mechanism* (stub-and-swap) is frozen; the specific number of days before the fallback triggers is a sprint-planning input. |
| **Prompt content and each module's specific evaluation dataset** | Domain and prompt-engineering work, explicitly out of architecture scope per the Blueprint's original boundary, unchanged here. |
| **The actual calibrated values** for the risk-to-coverage heuristic and the defect/flake escalation threshold | This document freezes that they are configuration, never hard-coded (Principle #4), and now freezes the *process* that will calibrate them (Accepted Change #6) — it does not and cannot supply the values themselves before real design-partner data exists. |
| **Per-module model routing table contents** | A cost/quality tradeoff decision that depends on model pricing and quality data current at implementation time, not at freeze time — the *mechanism* (LiteLLM, versioned config) is frozen; the table's contents are not. |
| **Connector-adapter implementation detail** for each of the four V1 tools | The contract is frozen; the adapter code behind it is Phase 2 implementation work by design. |
| **The specific reranker model/library** (Minor Improvement #1) | Deferred to the reranker's staged adoption trigger (Accepted Change #22) — naming a specific model before the retrieval-precision problem that justifies adding one has been observed would be premature. |
| **`Historical Failure Pattern (lite)` eager-vs-lazy computation** (Minor Improvement #2) | A Module 2 implementation detail below this document's level of resolution, flagged as a required input to Module 2's Phase 2 schema/query design. |
| **LightRAG → Microsoft GraphRAG migration path** (Moderate Concern #2) | Genuinely unresearched in any input document — whether an upgrade requires full re-indexing or can coexist incrementally is an open technical question, not an architecture decision this document can responsibly freeze without that research. Logged as a required Phase 2+ research item at the point GraphRAG adoption is actually being considered. |
| **The full debugging runbook** for correlating Langfuse, Temporal, the Neo4j browser, connector logs, and application logs during an incident (Major Risk #4) | Requires the actual deployed instrumentation to exist before a runbook can be accurate; freezing runbook content now would mean freezing fiction. **What is frozen now:** every service instruments through OpenTelemetry (Principle, unchanged), and this runbook is a named required deliverable before the Foundation sprint is called done — not an optional nicety. |
| **Data-residency and audit-log depth beyond WorkOS's baseline** (Moderate Concern #4) | A genuine Phase 2+ enterprise-hardening item, consistent with the Master Specification's own explicit deferral of "advanced security configuration" — unchanged by this document, and expected to surface in the first serious enterprise security review, as the Red Team predicted. |
| **A design spike at the Module 1/Module 3 seam** (fuzzy boundary between "what's ambiguous" and "what's a boundary condition") (Moderate Concern #1) | This document preserves the module boundary as frozen (per its own mandate not to redesign modules), but flags the spike as a required early-Module-1-or-3-sprint activity to confirm the boundary holds in practice, not to reopen it. |
| **The specific indirect-prompt-injection threat model's technical mitigations** beyond "a threat model and a red-team suite exist" (Accepted Change #12 names the requirement; the actual mitigations — input sanitization approach, allow-listing of downstream actions, etc. — are Phase 2 security-engineering work) | The requirement that this threat model exist is frozen and is a Sprint 0 deliverable; its specific technical content depends on implementation detail (exact prompt structure, exact downstream action set) not yet built. |

---

# Demo Scope Freeze

## What Version 1 contains

- All ten product modules per the Master Specification's confirmed, unchanged scope cut, with the Definitions of Done in **Final Module Definitions** above.
- The full ten-entity data model, **now including the Waived/Accepted Defect + Rationale attribute on the Internal Go/No-Go Document and Defect Report entities.**
- The full primary eight-step reasoning chain and the secondary production-feedback workflow, demonstrable end to end against the fixed demo app.
- Four connector adapters: Jira Cloud, GitHub, Slack, Playwright — real, demo-ready.
- Neo4j as the Knowledge Graph, **with `tenant_id` scoping enforced at Sprint 0** and native timestamps standing in for Graphiti's temporal-versioning layer.
- LangGraph-checkpointed orchestration; **Temporal not deployed at V1**, staged to a named trigger.
- Managed Langfuse (or plain OpenTelemetry export) during internal build; **self-hosted Langfuse required before the first real design-partner ticket or defect enters the system.**
- One mutation-testing engine (Stryker, matching the demo app's assumed JS/TS language).
- WorkOS tenant provisioning; **live per-partner SSO/SCIM configuration happens at onboarding, not before.**
- A per-tenant LLM cost ceiling in the gateway, a backup/DR policy on the graph and object storage, an on-call rotation for foundation-layer services, and an indirect-prompt-injection threat model with an accompanying red-team suite — **all four now Sprint 0 deliverables, not deferred.**
- A flat object-storage retention window (no tiering).
- Neo4j's native hybrid/vector search for retrieval (no dedicated reranker).

## What Version 1 explicitly does not contain

- Environment & Data Strategy (Module 99) — no entities, no code, disclosed to design partners as a sequencing bet, not a blind spot, per the Master Specification's own resolution.
- The richer Action-Item → ADR/Test-Case auto-generation form of Module 8 — narrow, risk-model-only closure only.
- Autonomous release triggering, in any form.
- Legacy execution-tool adapters (Selenium, Appium, BrowserStack) as real, working code — present only as a contract-test fake.
- Microsoft GraphRAG-style construction, or a migration path to it.
- A dedicated reranker model.
- Per-tenant physical database isolation in the Knowledge Graph (V1 uses software-enforced logical isolation; physical isolation is a named Phase 2+ upgrade).
- Object-storage retention tiering.
- Dynamic or learned LLM model routing (static, per-module routing only).
- Enterprise-grade admin, advanced security configuration (data residency, audit-log depth beyond WorkOS's baseline), multi-team/multi-tenant scaling beyond the logical isolation model above.
- Desktop packaging or on-prem/local inference.

## What triggers the transition from V1 staging to full production posture (V1 → "V1.1")

Each staged item above has a named trigger, consolidated here for a single point of reference:

| Staged item | Fires when... |
|---|---|
| Temporal (durable execution) | The product moves to unattended, always-on production usage, **or** a live design-partner deployment experiences a crash-related data-loss incident — whichever comes first |
| Self-hosted Langfuse | The first real design-partner ticket or defect record flows through the system |
| Graphiti temporal-versioning layer | A real "was this Risk Assessment Record still valid at time T" query is needed by a design partner or by Module 6/7 in earnest |
| Live WorkOS SSO/SCIM configuration | Per design partner, at onboarding |
| Dedicated reranker | The first real, observed retrieval-precision problem |
| Legacy connector adapters | A second real execution target is named by an actual design partner or prospect |
| Physical per-tenant graph database isolation | A real security review makes logical (software-enforced) isolation insufficient |
| Object-storage retention tiering | Real, observed storage-cost pressure |
| Synthetic eval/training data phase-out (per module) | The module's own defined real-data sample-count threshold is reached |

---

# Architecture Decision Records

### ADR-001 — Overall System Architecture
**Decision:** The system is one long-lived, checkpointed reasoning chain (ten modules as pipeline stages, not independent applications) wrapped in durable orchestration, reading from and writing to one shared Knowledge Graph, communicating exclusively through persisted state and a small number of shared-infrastructure contracts.
**Alternatives considered:** Ten independently deployed microservices communicating via direct API calls; a monolithic single-model-call product with no explicit module boundaries.
**Reasoning:** The product's differentiator — judgment that compounds with usage across a requirement's full lifecycle — has nowhere to live except a shared memory every stage reads and writes. Independent microservices calling each other directly would recreate tight coupling the moment Module 3 needs Module 2's output; a monolith with no module boundaries would make the demo's "watch each step reason independently" narrative impossible to build or evaluate.
**Consequences:** Every module is independently testable and independently swappable in principle, at the cost of requiring a genuinely shared, well-governed Knowledge Graph and orchestrator — which is why this document invests specifically in the graph's isolation and migration discipline rather than leaving it as a soft convention.

### ADR-002 — Repository Structure
**Decision:** A single monorepo (`qa-os/`), with shared logic in `packages/`, foundation services in `services/`, AI-reasoning logic in `modules/`, and prompts/evals mirrored per module.
**Alternatives considered:** A polyrepo with one repository per module or per service.
**Reasoning:** Ten modules sharing a schema, a graph client, an extraction backbone, and a rendering service would force those shared packages to be published and versioned across repository boundaries — real overhead for a pre-revenue team of this size, with no corresponding benefit since no module is planned for independent open-source release or separate deployment cadence at V1.
**Consequences:** Shared-package changes are atomic with their consumers, which is a genuine velocity win at this stage; the tradeoff (a monorepo can grow unwieldy at much larger team scale) is explicitly not a V1-stage risk and is not designed against here.

### ADR-003 — Technology Stack (Language and Runtime)
**Decision:** Python (FastAPI) for the backend and the entire AI-reasoning stack; TypeScript (Next.js/React) for the frontend only.
**Alternatives considered:** NestJS (TypeScript) for the backend, unifying the language across frontend and backend.
**Reasoning:** LangGraph, DSPy, and most of the evaluation tooling are Python-native. A TypeScript backend would force a language boundary between the API layer and the reasoning layer that FastAPI avoids entirely — the cross-language friction cost of a unified TypeScript stack is higher than the cost of maintaining one clean Python/TypeScript split at the frontend boundary, where it already has to exist regardless (`packages/schemas` codegen, ADR-004's near neighbor).
**Consequences:** The schema codegen toolchain (Pydantic → TypeScript, Final Technology Stack) exists specifically to keep this one necessary language boundary from becoming a source of drift.

### ADR-004 — Knowledge Graph: Database, Temporal Layer, and Tenant Isolation
**Decision:** Neo4j as the graph database, with Graphiti's temporal-fact-versioning layer staged to a named later trigger rather than adopted at Sprint 0; a single shared Neo4j instance with mandatory `tenant_id` scoping enforced exclusively in `kg-client`, not per-tenant physical databases, for V1.
**Alternatives considered:** Relational tables in Postgres with `valid_from`/`valid_to` columns as a temporal-versioning substitute (rejected — see Rejected Red Team Suggestions #1); per-tenant Neo4j Enterprise Edition databases for physical isolation (rejected for V1 on licensing-cost grounds, reserved as a Phase 2+ upgrade).
**Reasoning:** The ten-entity data model's relationship structure (execution history, environment telemetry, prior similar failures, cross-entity citation) is genuinely graph-shaped, and Modules 5 and 7 depend on multi-hop traversal that a relational substitute would have to re-implement as application-level joins — a worse migration position later, not a better one. Graphiti's specific value (temporal fact-versioning) is real but not needed until a real "was this still true at time T" query exists; V1's native timestamps are a genuine, honest proxy for a genuinely thin V1 graph. Physical per-tenant isolation is the cleaner long-term compliance story but carries real Enterprise-Edition licensing cost not justified before a real security review demands it; software-enforced logical isolation, with query access reduced to exactly one chokepoint, closes the actual risk (a missed filter causing cross-tenant leakage) without that cost.
**Consequences:** `kg-client` becomes the single most security-critical package in the codebase and must be treated accordingly (code review standard, test coverage standard) — this is a direct, accepted consequence of choosing the lower-cost isolation model, not a hidden one.

### ADR-005 — LLM Gateway and Model Routing
**Decision:** Self-hosted LiteLLM as the sole path from any module to any model provider; static, per-module model assignment as versioned configuration; a per-tenant cost ceiling with a defined fail-closed behavior on mid-chain exhaustion.
**Alternatives considered:** Portkey (stronger gateway-layer guardrails, revisit when enterprise security review demands them); OpenRouter (right for prototyping, wrong for steady state given per-token markup and data-residency questions); a learned/dynamic model router (rejected — savings smaller than static routing already captures, per the research consensus this plan treats as settled).
**Reasoning:** No module may reason about which model it's calling — that has to be a structural guarantee, not a policy, for per-module model swaps and cost tracking to remain a configuration change rather than a code change. The cost-ceiling requirement is new relative to the original plan and closes Major Risk #9 / Underengineering #1: a capability (LiteLLM *can* cap budgets) is not the same thing as a policy (what happens when it's hit).
**Consequences:** Every LLM-driven module must handle a fail-closed gateway response as a first-class case in its orchestration step, not an edge case — this is now a completion-criteria requirement for every module that calls the gateway.

### ADR-006 — Module Architecture and Boundaries
**Decision:** Ten product modules, each independently bounded, communicating only through persisted graph state or the orchestrator — never direct cross-module code imports.
**Alternatives considered:** A single-agent, tool-calling architecture where one LLM call decides which "capability" to invoke next, with no hard module boundaries.
**Reasoning:** The eight-step primary chain has two mandatory human-review gates and a hard constraint (a module's output must never verify itself) that has to be enforceable structurally. A single-agent architecture makes that constraint a prompt-level convention, not an architectural one — exactly the kind of thing the Red Team named as "the sort of thing that gets quietly relaxed in month four of a crunch." Ten bounded modules make the constraint a wiring fact instead.
**Consequences:** Module boundaries are frozen (this document's own mandate); the one acknowledged fuzzy seam (Module 1/Module 3, Moderate Concern #1) is flagged for an early validation spike, not a boundary change.

### ADR-007 — Evaluation Strategy
**Decision:** DeepEval as the CI regression gate, RAGAS for retrieval-specific metrics, Promptfoo for prompt-change regression and red-teaming, and mutation-testing engines (Stryker at V1) as the ground-truth correctness metric for generated test cases specifically — every LLM-driven module wired in from its first working version.
**Alternatives considered:** A custom, hand-rolled LLM-as-judge harness.
**Reasoning:** Three of ten modules sit near documented, research-confirmed accuracy ceilings (Module 2's coverage heuristic, Module 3's ~30–41% mutation-score ceiling, Module 5's classification ceiling). Evaluation is the only mechanism that verifies "V1-core done" claims are actually met rather than asserted. A custom harness would duplicate DeepEval/RAGAS's already-published, community-vetted metrics for no differentiated benefit.
**Consequences:** No prompt change merges without its eval suite passing (Principle #8) — and, per this document's addition, no module's synthetic eval data is a permanent substitute for real data past its own named threshold (Principle #24).

### ADR-008 — Configuration Philosophy
**Decision:** Any value expected to be recalibrated once real usage data exists — the risk-to-coverage heuristic, the defect/flake escalation threshold, per-module model routing, per-tenant cost ceilings — is versioned, tenant-overridable configuration from the moment it first appears, never a hard-coded constant "for now."
**Alternatives considered:** Hard-coding an initial value with a "TODO: make configurable" marker, common in early-stage builds.
**Reasoning:** Three specific values were already flagged upstream as unknowable today and certain to change; the Red Team confirmed this is applied consistently and correctly and should be defended, not revisited. This document extends the same philosophy to infrastructure *adoption timing* (Principle #21) — the staged-trigger table in Final Technology Stack is the config-over-code philosophy applied to "when do we turn this on," not just "what value does this hold."
**Consequences:** A calibration *process*, not just a calibration *value slot*, is now required before either of the two most credibility-sensitive values (Module 2's heuristic, Module 5's threshold) can be called calibrated rather than provisional (Accepted Change #6).

### ADR-009 — Prompt Architecture
**Decision:** DSPy as the programmatic prompt-optimization layer for rubric-scored extraction (Modules 1, 2, 5); every prompt lives in version control with an attached evaluation dataset in the same change; no module writes its own prompt-tuning logic.
**Alternatives considered:** CrewAI for rapid early prototyping (rejected as the production orchestrator — real teams migrate off it once precise state control is needed, which this product needs from Sprint 1, not as a later migration); hand-tuned prompts without a systematic optimization layer.
**Reasoning:** Turning a rubric plus labeled examples into a calibrated extraction prompt is the same underlying technique across the three modules that need it most; DSPy is the direct, purpose-built answer rather than hand-tuning by feel.
**Consequences:** DSPy's optimizers need real or real-quality labeled data that doesn't exist pre-launch — this is the direct reason Principle #24 (synthetic-to-real-data phase-out threshold) exists.

### ADR-010 — Deployment Strategy
**Decision:** Standard containerized cloud deployment (or an early-stage PaaS such as Fly.io/Render) as the V1 hosted-SaaS deployment model; no on-prem inference, no desktop packaging, for V1; Temporal and self-hosted Langfuse staged to named later triggers rather than deployed at Sprint 0.
**Alternatives considered:** Deploying the full "eventual" infrastructure footprint (Temporal, self-hosted Langfuse, WorkOS fully configured) simultaneously at Sprint 0.
**Reasoning:** QA-OS's V1 is explicitly a hosted product for design partners; deploying infrastructure ahead of the workload that needs it (an unattended, multi-tenant production load for Temporal; real design-partner data for self-hosted Langfuse) is exactly the kind of premature complexity the Red Team's Overengineering and Demo Optimization findings correctly identified.
**Consequences:** Deployment manifests (`infra/temporal/`, `infra/langfuse/`) are written and provisioned but not activated at Sprint 0 — this is a deliberate "ready but off" posture, not an unplanned gap, and each activation trigger is named in the Demo Scope Freeze table.

### ADR-011 — Multi-Tenancy Isolation Model
**Decision:** Logical, software-enforced tenant isolation in the Knowledge Graph for V1 — a single shared Neo4j instance, mandatory `tenant_id` on every node and relationship, enforced exclusively by `kg-client` as the only permitted query path — with physical per-tenant database isolation reserved as a named Phase 2+ upgrade.
**Alternatives considered:** Physical per-tenant Neo4j Enterprise Edition databases from Sprint 0; isolation "by convention" (every query author remembers to filter) with no enforced chokepoint.
**Reasoning:** This decision did not exist anywhere in the six input documents (Critical Issue #2) despite the product being repeatedly described as "hosted, multi-tenant SaaS" holding the most sensitive data in the system — defect reports, incident post-mortems, business-criticality assessments, for potentially competing customers. Isolation-by-convention is explicitly rejected: a single missed filter in a shared-graph model is a cross-tenant data leak, not a bug ticket, and "by convention" offers no structural guarantee against that. Physical per-tenant databases solve it more completely but at real, uncosted Enterprise-Edition licensing overhead not justified at design-partner scale.
**Consequences:** `kg-client` is now explicitly the single most security-critical package in the codebase (see ADR-004's consequence, restated here as this ADR's own primary consequence) and the schema-migration compatibility check (ADR covered under Principle #19) must specifically verify tenant-scoping is preserved on every schema change, not just structural correctness.

### ADR-012 — Module 7 Substrate / Product-Surface Split
**Decision:** Module 7 (Organizational QA Knowledge Graph) is split into two build phases with different sequencing priority: the substrate (schema, temporal layer proxy, read/write APIs) is foundation-layer infrastructure, built before Module 1 finishes; the product surface (natural-language query, Text-to-Cypher, citation) is a late-stage reasoning-module deliverable, built last among the ten modules.
**Alternatives considered:** Treating Module 7 as "the seventh module to build" in numeric sequence, with substrate and surface built together at that point.
**Reasoning:** Module 7's substrate is a dependency of Modules 1, 2, 5, 6, and 8 — it has to exist before the first of those writes to it. Its product surface, by contrast, is only demo-worthy once the graph holds real, multi-module data; building the natural-language query UI against a near-empty graph would understate the module's actual value and risk a weak demo moment through no fault of the underlying retrieval technology.
**Consequences:** This is, in the Red Team's own assessment, "the single best sequencing decision in the plan." This ADR formalizes it as a permanent decision record per Minor Improvement #4, rather than leaving it as prose scattered across the Development Master Plan and Blueprint.

---

# Engineering Freeze Checklist

| Area | Status | Note |
|---|---|---|
| **Architecture** | ✅ Frozen | Complete subsystem, service, and data-flow definitions above; the one structural addition (schema-migration discipline applied to the graph) is itself frozen, not left open. |
| **Technology** | ✅ Frozen | One decision per layer, no debated alternatives left open; staged-adoption items have named, checkable triggers, not vague "later" language. |
| **Repository** | ✅ Frozen | Package/service boundary fixed; internal-to-package layout correctly left to Phase 2 implementation. |
| **Module Boundaries** | ✅ Frozen | All ten modules unchanged from the Master Specification's scope cut; the one acknowledged fuzzy seam (Module 1/3) is flagged for a validation spike, not reopened. |
| **Interfaces** | ✅ Frozen | Connector, graph, gateway, and rendering contracts unchanged; the graph schema is now held to the same interface discipline as the connector contract. |
| **Shared Infrastructure** | ✅ Frozen | Full list above, with five items (graph isolation/migration, gateway cost governance, config calibration process, observability hosting stage, on-call ownership) closed relative to the Blueprint's original scope. |
| **Knowledge Layer** | ✅ Frozen | Database, temporal-layer staging, and — closing the review's top blocking concern — tenant isolation are all decided. |
| **Prompt Architecture** | ✅ Frozen | DSPy plus versioned prompt store, unchanged; synthetic-data phase-out threshold now a required per-module completion criterion. |
| **Evaluation** | ✅ Frozen | Stack unchanged; synthetic-to-real-data switchover criterion closes the one open process gap. |
| **Configuration** | ✅ Frozen | Config-over-code philosophy unchanged and defended; a real calibration process (not just a value slot) now exists for the two highest-credibility-risk values. |
| **Dependencies** | ✅ Frozen | Module dependency graph unchanged; Foundation's critical path is de-risked (two of seven components removed from it) without changing any module's actual dependencies. |
| **Implementation Order** | ✅ Frozen | Development Master Plan's sequence (Foundation → Module 10 → Module 7 substrate → Modules 1–6 → Module 7 surface → Module 8, Module 9 continuous) unchanged; a stub-and-swap fallback is added at the Foundation boundary, not a reordering. |
| **Testing Strategy** | ✅ Frozen | Eval harness and mutation-testing approach unchanged; scoped to one mutation engine at V1 with an explicit, named assumption (demo app language) stated rather than left implicit. |
| **Demo Scope** | ✅ Frozen | Full V1-contains / V1-does-not-contain / staged-trigger tables above — no ambiguity left for a sprint planner to resolve. |
| **Engineering Principles** | ✅ Frozen | 24 principles, 18 carried forward unchanged, 6 new, all numbered and none contradicting each other. |
| **Acceptance Criteria** | ✅ Frozen | Every module's Definition of Done is stated; the two modules whose criteria changed (5 and 6, for the new attribute; 8, for the validation-spike gate) are marked as changed, not silently updated. |

**Every checklist item is frozen. None requires revision before Sprint 0 begins.**

---

# Final Verdict

## APPROVED FOR IMPLEMENTATION

This is a stronger verdict than the Red Team's own "YES, WITH CHANGES," and that upgrade is earned, not asserted: the changes the Red Team called for are not scheduled as follow-up work in this document — they are incorporated directly into the frozen architecture itself. There is no longer a "before Sprint 0" list sitting outside the specification; the specification now includes the fixes.

**Why not "APPROVED WITH MINOR FIXES" instead:** that verdict would imply real architectural work remains before implementation can safely begin. It doesn't. The three items the Red Team would have blocked a Sprint 0 kickoff over — the missing waived-defect-rationale attribute, the undecided tenant-isolation model, and the absent schema-migration discipline — are each fully decided above, not partially sketched. What remains (the items in Deferred Decisions) are, without exception, either Phase 2 implementation detail this document was never meant to resolve, or open research questions no input document had the evidence to close responsibly. Calling those "minor fixes" still owed would misdescribe what they actually are.

**Why not "NOT READY":** the underlying architecture was already sound before this document — the Red Team's own assessment, "This is not a team that doesn't know what it's doing," is accurate and is reaffirmed here. Config-over-code discipline, the connector interface designed before implementation, three architecturally-enforced human-in-the-loop non-negotiables, and a disciplined refusal to over-build where the research ceiling is already known to be low are not the marks of an unready project. They are the marks of a project that had, in a small number of specific, nameable places, let documentation ceremony substitute for finishing the harder engineering questions — and this document is that finishing work.

**What makes this verdict trustworthy rather than optimistic:** every fix above traces to a specific, named Red Team finding, and every finding was individually triaged as Accepted, Rejected, or Deferred with stated reasoning — nothing was smoothed over, and one suggestion (replacing Neo4j) was explicitly rejected rather than reflexively adopted, which is itself evidence this freeze was not simply rubber-stamping the review. The health-score movement (6.5 → 8.5) reflects three closed Critical Issues, nine closed Major Risks and Underengineering findings, and a clear, checkable staging plan for the remainder — not a re-scoring of the same open items under friendlier language.

Sprint 0 may begin against this document.

---

# HANDOFF

## Sprint Planner Inputs

Everything below is immutable. The Sprint Planner decomposes it into sprints and tasks; it does not redesign any of it.

**Modules (build, not redesign):** ten frozen modules per **Final Module Definitions** — Requirement Intelligence, Risk & Test Strategy, Test Design & Generation, Execution Orchestration, Defect Intelligence & Triage, Release Readiness & Go/No-Go, Organizational QA Knowledge Graph (substrate + surface), Production Feedback & Learning Loop, QA Command Center, Integration & Extensibility. Environment/Data Strategy is Phase 2+, not a Sprint Planner input at all.

**Build order (frozen):** Foundation → Module 10 → Module 7 (substrate) → Module 1 → Module 2 → Module 3 → Module 4 (Temporal *scaffolded, not activated*) → Module 5 → Module 6 → Module 7 (product surface) → Module 8. Module 9 built incrementally throughout, hardened as a final pass.

**Foundation scope (frozen, with the fallback named):** connector interface, Neo4j graph substrate (schema + `tenant_id` enforcement in `kg-client`, no Graphiti), PostgreSQL, WorkOS tenant provisioning (no live SSO/SCIM config yet), self-hosted LiteLLM, LangGraph skeleton, Eval CI (DeepEval/RAGAS/Promptfoo), per-tenant LLM cost ceilings, a backup/DR policy for the graph and object storage, an on-call rotation assignment, and an indirect-prompt-injection threat model plus red-team suite. `kg-client` and the auth check ship with stub implementations from day one, swappable to real backends without blocking downstream module work.

**Data model (frozen):** the ten-entity schema (Requirement, Test Case, Observation/Execution Result, Defect Report, ADR, Internal Go/No-Go Document, Triage/Strategy Decision Record, Production Incident/Post-Mortem, Risk Assessment Record, Historical Failure Pattern-lite), **plus the Waived/Accepted Defect + Rationale attribute on Internal Go/No-Go Document and Defect Report**, under an additive-only migration discipline with a mandatory compatibility check on every change.

**Technology stack (frozen):** as specified in full in **Final Technology Stack**, including every staged-adoption trigger. The Sprint Planner schedules infrastructure work against the *staged* timing (e.g., no Temporal deployment task in the Module 4 sprint; a Temporal *readiness* task instead, activated later).

**Engineering principles (frozen):** all 24 principles in **Final Engineering Principles** apply without exception to every sprint's work, including the six added by this document (schema migration discipline, `kg-client` as sole query chokepoint, named infrastructure-adoption triggers, on-call ownership, per-tenant cost governance, synthetic-data phase-out thresholds).

**What the Sprint Planner must schedule that did not exist as a task before this document:** (1) the Waived/Accepted Defect + Rationale schema addition, in Module 7's substrate sprint, before Module 5 or 6 is built against the old shape; (2) the `kg-client` tenant-scoping enforcement layer and its test coverage, in the same sprint; (3) the schema-compatibility-check harness, in Foundation; (4) the Module 8 validation spike, as a checkpoint before Module 8's build sprint, with a real possible outcome of re-scoping that module to Human-Only; (5) the indirect-prompt-injection threat model and red-team suite, in Foundation, before Module 1 is exposed to real ticket content; (6) the backup/DR policy definition for the graph and object storage, in Foundation; (7) the on-call rotation assignment, in Foundation; (8) the calibration-process definition (owner, minimum sample size, disagreement rule) for Module 2 and Module 5's provisional values, before either module's sprint is called complete; (9) the schema codegen toolchain setup (`datamodel-code-generator`/`quicktype`), in Foundation, alongside `packages/schemas`.

**What the Sprint Planner must never re-open:** any module boundary; any entity in the ten-entity data model; the V1/Phase-2+ scope cut, including Environment & Data Strategy's deferral; the agent/human responsibility split and its three non-negotiable human-in-the-loop gates; the choice of Neo4j as the graph database (Graphiti's *timing* is staged, the database itself is not); the choice to buy, not build, authentication; the build order above; or any item marked ✅ Frozen in the Engineering Freeze Checklist.

Every subsequent engineering conversation on this project should begin with: **"Given Engineering_Freeze_v1.0..."**
