# Roadmap — Sprint & Epic Plan

> **Status: the original plan, not the build history.** This document lays
> out the sprint sequence for building the full 10-module system in order
> (Foundation → Module 10 → Module 7 substrate → Modules 1–8 → Integration
> Hardening). **That sequence was not what actually happened.** What actually
> got built skipped straight to Modules 1–3 via direct hardening/wiring
> passes on existing scaffolding — no Foundation sprint, no Module 10 sprint,
> no Module 7 substrate sprint were ever run as their own phase. See the
> top-level `README.md` §4–§8 for the real build history and current status.
> Treat this doc as **the plan for finishing the other 6 modules from here**,
> not as a record of what's done.

Turns the frozen architecture (`02_engineering_spec.md`) into a numbered sprint
sequence: single-owner Epics, dependencies, shared-infrastructure allocation,
and merge-conflict boundaries. Sprint order follows module order (Foundation →
Module 10 → Module 7 substrate → Modules 1–8 in dependency order → Integration
Hardening).

---

# **Part 1 — Implementation Philosophy**

## **1.1 Sprint order is module order, with one exception**

The frozen build order — Foundation → Module 10 → Module 7 (substrate) → Module 1 → Module 2 → Module 3 → Module 4 → Module 5 → Module 6 → Module 7 (surface) → Module 8, with Module 9 continuous throughout — is not renegotiated here. It is made concrete: **each build-order item becomes exactly one sprint, in the same order.** No item is split across two sprints; no two items are merged into one. Sprint number is build-order position and nothing else.

The one exception is Module 9. The Freeze states Module 9 is "built incrementally in parallel with every other module, hardened as a final integration pass" — explicitly not a pipeline stage. Sprint Architecture honors that literally: Module 9 gets no dedicated sprint slot in the primary sequence. Instead it runs as a **continuous track** — one small epic per sprint, Sprint 0 through Sprint 10, plus a dedicated final-hardening epic in Sprint 11. Giving Module 9 its own numbered sprint would silently reorder it into the pipeline sequence the Freeze explicitly says it is not part of.

This produces twelve sprints (0–11) for eleven build-order items: eleven sequential module/foundation sprints, plus Sprint 11 as a dedicated integration-hardening sprint — the one pass every reasoning module needs together, not just individually, which the Freeze's module list implies (three human-review gates, one self-verification rule, one shared rendering path) but does not name as its own build-order line.

## **1.2 Why this order minimizes engineering risk**

A sprint boundary that exactly matches a module boundary means "what am I building" and "when is it safe to start" have the same answer for every team and every AI coding session: read one module's definition in the Freeze, read one sprint's Epics here, start. No sprint requires finishing half a module, waiting, and returning for the second half — the kind of split that reliably produces half-integrated state and forgotten follow-up work.

Foundation is the one sprint that is not a single module — and it is also the sprint the Freeze itself flagged as the project's single biggest schedule risk (Critical Issue #4: a serialized seven-system big-bang). Sprint Architecture resolves that risk the way the Freeze resolved it architecturally: not by shrinking Foundation's scope, but by splitting it into fourteen independently-ownable Epics (Part 3), nearly all of which run fully in parallel because they touch disjoint folders, disjoint packages, and disjoint people. Where the Freeze already named a stub-and-swap fallback (`kg-client`, the auth check), Sprint Architecture keeps it a genuine non-blocking dependency, not a checkbox: Sprint 3 (Module 1) does not wait for Sprint 2 (Module 7 substrate) to reach full completion of the real Neo4j backend before Module 1 implementation can begin — it begins against the same stub interface Foundation shipped, and the swap to the real backend is a Sprint-3 integration checkpoint, not a Sprint-3 starting gate. This is the Foundation-boundary fallback generalized one level down the build order, and it is applied a second time at the Module 5 ↔ Module 7 boundary (Part 3, Epic M5.0) on the Implementation Audit's own recommendation (Modularity Audit, Exception 1) — the same mechanism, reused, not reinvented.

## **1.3 Why this order minimizes AI coding conflicts**

Every module folder (`modules/module-0X/`) has exactly one owning Epic per sprint and communicates with the rest of the system only through `packages/*` and persisted graph state — never a direct import of another module's internals (Principle #6). An AI coding session scoped to one Epic can be given read access to `packages/*` and its own module folder and nothing else; there is no folder it could reach into that a different session, working a different Epic in the same sprint, is also writing to. Two AI agents cannot silently diverge on the same file because neither is ever pointed at the same file as the other.

The one place this isn't automatically true is `packages/schemas` — the single artifact every module depends on. This is why schema changes are their own gated event, never incidental to whichever module happens to need a new attribute: every schema change runs through the compatibility-check harness (built in Foundation, first exercised in Sprint 2) before it merges, and `packages/schemas` is Human-Owned per the Implementation Audit's Code Ownership Matrix — no AI coding session is ever the last reviewer on a change to the one file every other Epic's generated code imports.

The same discipline resolves the two AI-specific boundary risks the Implementation Audit names (Modularity Audit): the Module 1 ↔ Module 3 seam, and the per-module trust-indicator shape. Both are encoded as explicit Pydantic contracts in `packages/schemas` *before* the modules that depend on them are implemented (Sprint 3, Epic M1.0b; Sprint 2, Epic M7S.5) — not left as prose in a design doc for two independently-prompted AI sessions to each interpret their own way.

## **1.4 Why this order minimizes debugging**

Every LLM-driven Epic ships with its evaluation dataset attached in the same sprint (Principle #8), so a broken module surfaces in its own sprint's CI gate, not three sprints later in an end-to-end demo rehearsal. Module 3's mutation-testing pass (Sprint 5) and the schema compatibility-check harness (first exercised Sprint 2, mandatory thereafter) exist for the same reason: catch a wrong test-case generation or a breaking schema change at the sprint that introduced it, not at integration.

The Implementation Audit surfaces one debugging risk the architecture layer could not see: a DSPy or LangGraph dependency bump can silently shift compiled-prompt behavior with no diff visible in a normal code review of the source signature (Implementation Rules A3–A4). Sprint Architecture treats a dependency bump on either package the same way it treats a prompt-content change: it re-runs the full eval suite as a merge gate, in every sprint that touches that package, not only the sprint that first introduced it (see Part 8).

## **1.5 Foundation: fourteen systems, not one big bang**

The Red Team's Critical Issue #4 named Foundation as a serialized seven-system big-bang; the Freeze de-risked it by removing two systems from the critical path (Graphiti, Temporal) and naming a stub-and-swap fallback for the rest. Sprint Architecture completes that de-risking at the sprint-planning layer: Foundation is not one Epic, or even seven — it is **fourteen Epics** (Part 3, Sprint 0), one per system or concern, each independently ownable, and all but one (Operational Readiness, which documents the other thirteen's outputs) with no hard dependency on any other Foundation Epic finishing first. A slip in graph-infrastructure provisioning does not stall LLM-gateway work; a slip in the security threat-model does not stall the schema-codegen toolchain. This is the concrete mechanism behind Sprint 0 carrying visible, parallel progress from day one rather than a single serialized countdown.

## **1.6 Document authority in this phase**

Nothing in Parts 2–10 below is an architecture decision. Every sprint, every Epic, every dependency edge, and every ownership assignment traces to a specific line in `Engineering_Freeze_v1.0.md` or `Implementation_Audit.md`. Where this document had to make a genuine sprint-planning judgment call the two source documents left open — Epic granularity within a sprint, which sub-lead owns which Foundation Epic, exact prompt-numbering ranges — that judgment is scoped to *this layer only* and is itself frozen once stated here, per the same "decide once, don't re-litigate" discipline the Freeze applied to technology choices.

---

---

# **Part 2 — Sprint Roadmap**

A "Sprint" here is a scoped unit of work bounded by its own completion criteria, not a fixed calendar duration. Assigning calendar length (including the exact Sprint 0 stub-and-swap timebox before its fallback triggers) requires real team-capacity input this document does not have, and is correctly left as a Deferred Decision in the Freeze — Phase 3 or the team's own capacity planning sets it, not architecture or sprint-mapping work.

## **Sprint 0 — Foundation**

**Purpose:** Stand up every foundation-layer system the ten reasoning modules depend on, with stub/fake implementations at the two highest-schedule-risk points (`kg-client`, the auth check) so no downstream module is blocked on every one of Foundation's fourteen systems landing simultaneously.

**Objectives:**

* Provision the connector interface, graph infrastructure, relational store, authentication, LLM gateway, orchestration skeleton, evaluation harness, schema/codegen toolchain, configuration service, observability, object storage, security threat model, operational readiness, and frontend/design-system shell — one Epic each (Part 3).  
* Pin every dependency version named in the Implementation Audit's Technology Audit table; freeze the monorepo on Python 3.12 and Node 22.x LTS.  
* Ship `kg-client` and the auth check as swappable stubs, per the Freeze's own Foundation fallback.

**Expected deliverables:** a running monorepo skeleton (`qa-os/`) with every package/service folder present; a provisioned (empty-schema) Neo4j 5.26.x Enterprise instance; a provisioned PostgreSQL 16.x instance; a WorkOS tenant, unconfigured for live SSO/SCIM; a pinned, signature-verified self-hosted LiteLLM deployment with a stubbed per-tenant cost-ceiling config; a LangGraph skeleton with no module logic wired in; DeepEval/RAGAS/Promptfoo running as an empty-suite CI gate; the `packages/schemas` Pydantic-authoring pattern and its quicktick-based codegen pipeline, wired as a CI-atomic step; the schema compatibility-check harness mechanism (unexercised — first real schema doesn't exist until Sprint 2); `packages/config-service` scaffolded; OpenTelemetry \+ `structlog` \+ managed Langfuse wired across every service; S3-compatible object storage with a flat retention window and a backup/DR policy; a written indirect-prompt-injection threat model plus a portable (non-Promptfoo-coupled) red-team scenario set; a named, paged on-call rotation for all seven foundation-layer services; a v0 debugging runbook; a Next.js/shadcn/Tailwind frontend shell.

**Demo milestone:** a synthetic ticket, injected directly into the stub connector, flows through the stub `kg-client` and the LangGraph skeleton and appears as an unstyled trace entry in the Command Center shell — proving the pipeline's wiring is alive end to end, before any module contains real reasoning logic. This satisfies Part 9's "no invisible infrastructure-only sprint" requirement for the one sprint that is hardest to make visible.

**Definition of Done:** every Epic in Part 3, Sprint 0 meets its own completion criteria; every Part 8 verification gate passes; the on-call rotation has a named owner with a real pager; the debugging runbook exists (v0, to be finalized against real instrumentation later); every version in the Technology Audit table is pinned in a committed lockfile (`uv.lock`, `pnpm-lock.yaml`); `kg-client` and the auth check are stub-quality and explicitly documented as such, not silently assumed complete.

## **Sprint 1 — Module 10: Integration & Extensibility Layer**

**Purpose:** Build the literal front door — the four V1 connector adapters behind the Foundation-built contract — since nothing downstream reasons about anything until an external event is ingested.

**Objectives:** implement Jira Cloud, GitHub, Slack, and Playwright adapters against `packages/connector-contract`; prove the contract's generality via a fake legacy adapter in the contract's own test suite, without writing real Selenium/Appium/BrowserStack code.

**Expected deliverables:** four demo-ready adapters; a passing legacy-adapter contract-test fake; OpenAPI-to-Pydantic codegen wired for each of the three ticket/PR/chat tool's request-response models (via `datamodel-code-generator`, repurposed per the Implementation Audit's toolchain correction).

**Demo milestone:** a real Jira ticket, a real GitHub PR event, and a real Slack message each round-trip through their adapter and land as a normalized internal event visible in the Command Center's raw event log — the front door is real, even though nothing reasons about the content yet.

**Definition of Done:** all four V1 adapters demo-ready per the Freeze's Module 10 Definition of Done; legacy adapters present behind the contract only, as a contract-test fake, never real code; every Part 8 gate passes.

## **Sprint 2 — Module 7 (Substrate): Organizational QA Knowledge Graph**

**Purpose:** Make the Knowledge Graph real. Author the ten-entity schema, swap `kg-client` from Foundation's stub to a real, tenant-scoped Neo4j-backed client, and exercise the schema compatibility-check harness for the first time — before the first reasoning module (Module 1) writes a single entity.

**Objectives:** author the ten-entity schema (including the Waived/Accepted Defect \+ Rationale attribute) in `packages/schemas`; enforce `tenant_id` scoping exclusively inside `kg-client`; wire LightRAG-style construction; decide the shared trust/confidence-indicator schema before Module 2's sprint needs it; scaffold the Rendering/Citation service.

**Expected deliverables:** a live ten-entity graph schema; a real `kg-client` that is the only code path permitted to issue a Cypher query; a passing first exercise of the compatibility-check harness; a shared trust-indicator Pydantic type in `packages/schemas`; a `packages/rendering` scaffold.

**Demo milestone:** a synthetic Requirement entity, written directly via `kg-client`, is retrievable with its `tenant_id` correctly scoped, and a second synthetic tenant's write is provably invisible to the first tenant's read — the graph is alive, isolated, and schema-governed, even though no reasoning module has touched it yet.

**Definition of Done:** per the Freeze's Module 7 substrate Definition of Done — the schema is live, Modules 1 and 2 (built next) can read/write against it without a schema change, and tenant scoping is enforced before any second tenant's data is written; every Part 8 gate passes.

## **Sprint 3 — Module 1: Requirement Intelligence**

**Purpose:** Build the first reasoning module — the one everything downstream depends on — after resolving the two decisions the Implementation Audit flagged as required before this sprint can start cleanly: the Claude Agent SDK's tool-scoping posture, and the Module 1 ↔ Module 3 boundary contract.

**Objectives:** make and record the Claude Agent SDK scoping decision; encode the Module 1/3 boundary as a Pydantic contract; build the ambiguity/gap-taxonomy extraction logic; wire ingestion-to-graph-write; attach Module 1's evaluation dataset.

**Expected deliverables:** a recorded Agent-SDK scoping decision (Epic M1.0a); a `packages/schemas` boundary contract (Epic M1.0b); a working Module 1 DSPy signature; human-review-gated clarifying questions and draft acceptance criteria written back to the Requirement entity.

**Demo milestone:** one realistic Jira ticket, ingested through Module 10's real adapter, produces clarifying questions and draft acceptance criteria from a visibly-fired checklist item, presented as an editable, human-reviewable artifact in the Command Center.

**Definition of Done:** per the Freeze's Module 1 Definition of Done, unchanged; every Part 8 gate passes; the Agent SDK decision and the M1/3 boundary contract are both recorded before this sprint's other Epics begin (Part 4).

## **Sprint 4 — Module 2: Risk & Test Strategy Engine**

**Purpose:** Build change-risk assessment and coverage-depth recommendation, and put a real calibration process — not just a value slot — behind the single largest live credibility risk in the product.

**Objectives:** implement Risk Exposure scoring; wire historical-defect-density graph queries; define the calibration process (named owner, minimum sample size, disagreement rule) for the risk-to-coverage heuristic; wire the heuristic into `config-service`.

**Expected deliverables:** a working Module 2 DSPy signature; a Risk Assessment Record write path with a graph-sourced rationale sentence; a documented, owned calibration process.

**Demo milestone:** a repo diff plus a validated Requirement produces a Risk Assessment Record with one sentence of rationale citing an actual graph-sourced number, visible in the Command Center's new Risk Assessment surface, with the heuristic swappable via config without a redeploy.

**Definition of Done:** per the Freeze's Module 2 Definition of Done; the calibration process is documented and owned before this sprint is called complete (Freeze Handoff item 8); every Part 8 gate passes.

## **Sprint 5 — Module 3: Test Design & Case Generation**

**Purpose:** Build test-case generation against the now-resolved Module 1/3 boundary contract, with the mutation-testing feedback loop as the correctness signal, not a better prompt.

**Objectives:** implement functional/boundary/negative test-case generation; wire the generate → mutate → discard → review loop against Stryker; enforce human-approval-only persistence.

**Expected deliverables:** a working Module 3 generation pipeline; a Stryker CI integration; a human-review UI backend for candidate test cases; a captured mutation-score baseline.

**Demo milestone:** given a Risk Assessment Record, Module 3 generates candidate test cases, runs at least one real mutation-testing pass against the demo app, and presents mutation-surviving candidates as an editable, reviewable set — no auto-commit path exists.

**Definition of Done:** per the Freeze's Module 3 Definition of Done; every Part 8 gate passes, including the mutation-score baseline capture.

## **Sprint 6 — Module 4: Execution Orchestration Layer**

**Purpose:** Run the approved suite and enforce, structurally, that a module's own test result is never the sole gate on its own related fix — with the durable-execution layer scaffolded, not activated.

**Objectives:** wire suite triggering through Module 10's Playwright adapter; persist Observation/Execution Result entities; implement the self-verification gate as an orchestration state-machine rule; scaffold Temporal behind a feature flag.

**Expected deliverables:** live suite execution against the fixed demo app with streamed progress; a working self-verification gate independent of Temporal; a provisioned-but-inactive Temporal deployment manifest.

**Demo milestone:** the approved test suite runs live against the fixed demo app with progress streaming to the Command Center, and a deliberately-failing case demonstrates the self-verification firewall refusing to let the module's own passing result stand in for independent proof.

**Definition of Done:** per the Freeze's Module 4 Definition of Done; the self-verification gate is demonstrably enforced regardless of Temporal's (inactive) presence; every Part 8 gate passes.

## **Sprint 7 — Module 5: Defect Intelligence & Triage**

**Purpose:** Build defect-vs-flake classification and business-severity judgment, decoupled from Module 7's still-unbuilt product surface via the same stub-and-swap discipline used at the Foundation boundary.

**Objectives:** build a fixture-backed fake graph-context provider; implement reproducibility judgment and defect-vs-flake classification; wire the Waived/Accepted Defect \+ Rationale attribute; define the escalation-threshold calibration process; swap to Module 7's real retrieval path once validated.

**Expected deliverables:** a working Module 5 DSPy signature; a Defect Report write path including the waived-defect attribute; a documented calibration process for the escalation threshold; a validated real-retrieval swap-in.

**Demo milestone:** a failing Observation/Execution Result produces a reproducibility judgment, a defect-vs-flake call with a calibrated confidence score, and — where applicable — a waived-defect rationale, visible in the Command Center's new Defect Triage surface.

**Definition of Done:** per the Freeze's Module 5 Definition of Done, plus the new attribute; the calibration process is documented and owned before this sprint is called complete; every Part 8 gate passes.

## **Sprint 8 — Module 6: Release Readiness & Go/No-Go Advisor**

**Purpose:** Aggregate everything upstream into a cited, advisory-only Internal Go/No-Go Document — the least open-research-risk module of the ten, built as templated aggregation over the shared rendering service.

**Objectives:** implement go/no-go aggregation logic; surface waived-defect rationale as a first-class completion criterion; integrate the Rendering service; post an advisory GitHub Check Run via Module 10's adapter.

**Expected deliverables:** a working aggregation pipeline; a rendered, cited Internal Go/No-Go Document; a posted advisory Check Run.

**Demo milestone:** the Risk Assessment Record, accumulated Test Case/Observation results, and open Defect Reports aggregate into one cited go/no-go brief, visibly surfacing any waived-defect rationale, rendered in the Command Center and posted as an advisory (never autonomous) GitHub Check Run.

**Definition of Done:** per the Freeze's Module 6 Definition of Done (changed): the brief visibly surfaces waived-defect rationale as a completion criterion, not an incidental side effect; every Part 8 gate passes.

## **Sprint 9 — Module 7 (Product Surface): Natural-Language Query**

**Purpose:** Build the Knowledge Graph's product-facing surface once the graph actually holds real, multi-module data — deliberately last among the ten modules' surfaces, per ADR-012, so the demo doesn't understate a thin, near-empty graph.

**Objectives:** implement Text-to-Cypher query; ground every answer in a specific cited entity; capture a retrieval-precision baseline informing the (still-staged) reranker trigger.

**Expected deliverables:** a working natural-language query path; citation-grounded answer rendering via `packages/rendering`; a captured retrieval-precision baseline.

**Demo milestone:** a natural-language question matching the demo script returns an answer citing the specific grounding entity — never unattributed prose — in the Command Center's new Knowledge Query surface.

**Definition of Done:** per the Freeze's Module 7 surface Definition of Done: a natural-language query matching the demo script returns a cited answer; every Part 8 gate passes.

## **Sprint 10 — Module 8: Production Feedback & Incident Learning Loop**

**Purpose:** Close the feedback loop — deliberately narrow, deliberately last, and gated on a validation spike before any implementation begins, since this module sits nearest the pipeline's thinnest evidence base.

**Objectives:** run the AI-Augmented-vs-Human-Only validation spike as a go/no-go checkpoint; if the spike clears, capture Production Incident entities, extract action items, and update the affected Risk Assessment Record and Historical Failure Pattern-lite counter.

**Expected deliverables:** a recorded validation-spike outcome; if AI-Augmented is confirmed, a working incident-capture and action-item-extraction pipeline; if not, a recorded re-scope to Human-Only with the reasoning attached.

**Demo milestone:** a manually-entered Production Incident produces extracted action items that visibly update the affected component's Risk Assessment Record, closing the loop the next time a Requirement touches that component — demonstrated live in the Command Center's Feedback Loop surface.

**Definition of Done:** per the Freeze's Module 8 Definition of Done, plus the validation-spike process addition (Accepted Change #9); every Part 8 gate passes.

## **Sprint 11 — Integration Hardening & Demo Readiness (Demo Complete)**

**Purpose:** The one pass every reasoning module needs together, not just individually — Module 9's final hardening, a full end-to-end rehearsal, and closing every operational loose end Foundation opened but could not finish alone (security, cost governance, on-call, staged-adoption tracking).

**Objectives:** harden Module 9 into its final role-aware form; rehearse the full eight-step primary chain plus the feedback-loop workflow end to end; finalize the security red-team pass against the fully assembled system; load-test the per-tenant cost ceiling's fail-closed behavior; validate the debugging runbook against a simulated multi-service incident; confirm the staged-adoption tracker is live.

**Expected deliverables:** a hardened Command Center with QA Engineer and QA Lead views, per-module trust indicators shown separately (never blended); a rehearsed, demo-ready end-to-end run; a finalized red-team pass; a validated fail-closed cost-ceiling behavior; a validated runbook; a confirmed staged-adoption tracker.

**Demo milestone — Demo Complete:** the full primary eight-step reasoning chain and the secondary production-feedback workflow run live, end to end, against the fixed demo app, exactly as scoped in the Freeze's Demo Scope Freeze table — this is the sprint the entire roadmap has been building toward.

**Definition of Done:** every module's own Definition of Done (Sprints 1–10) still holds under integrated load; every Part 8 gate passes; the Demo Scope Freeze's full "What V1 contains" list is demonstrable in one continuous run.

---

# **Part 3 — Epic Breakdown**

Format for every Epic: Owner, Purpose, Dependencies, Outputs (build artifacts produced), Consumes (interfaces/data read from elsewhere), Produces (runtime data/entities this Epic's code causes to exist), Shared packages used, Modules affected, Completion criteria. Fields are kept terse by design — this is a reference table, not prose.

## **Sprint 0 — Foundation Epics**

#### **F1 — Connector Contract Definition**

* **Owner:** Foundation pod / Connector sub-lead  
* **Purpose:** Define the one internal `Connector` interface (authenticate, subscribe, fetch, post-status-back) before any tool-specific adapter exists.  
* **Dependencies:** none.  
* **Outputs:** `packages/connector-contract`.  
* **Consumes:** nothing.  
* **Produces:** an interface, no runtime data.  
* **Shared packages used:** none (this Epic *is* the shared package).  
* **Modules affected:** Module 10 (direct consumer, Sprint 1); Modules 1, 4, 6 (indirect consumers via Module 10's adapters).  
* **Completion criteria:** contract compiles; a fake adapter implementing it passes a generic contract test suite with zero tool-specific code.

#### **F2 — Graph Infrastructure Provisioning \+ `kg-client` Stub**

* **Owner:** Foundation pod / Graph sub-lead  
* **Purpose:** Provision an empty-schema Neo4j 5.26.x Enterprise instance and ship a stub/fake `kg-client` so downstream Epics are never blocked on real graph provisioning.  
* **Dependencies:** none.  
* **Outputs:** a running Neo4j 5.26.x Enterprise LTS instance (not the CalVer rolling line); `packages/kg-client` v0 (in-memory fake, same public interface the real client will expose).  
* **Consumes:** nothing.  
* **Produces:** no real entities yet (stub returns fixture data).  
* **Shared packages used:** none.  
* **Modules affected:** every module that reads/writes the graph (1, 2, 5, 6, 7, 8) consumes `kg-client`'s interface starting Sprint 2 onward.  
* **Completion criteria:** Neo4j instance reachable; `neo4j` driver pinned to 5.28.x; stub `kg-client` exposes the exact public method signatures the real client will implement in Sprint 2, so no consumer code changes at swap time.

#### **F3 — Relational Store Provisioning**

* **Owner:** Foundation pod / Data sub-lead  
* **Purpose:** Provision PostgreSQL for tenant/user/billing state, connector configuration, and versioned calibration values.  
* **Dependencies:** none.  
* **Outputs:** a running PostgreSQL 16.x instance; `infra/postgres/` migration tooling.  
* **Consumes:** nothing.  
* **Produces:** empty relational schema (no business tables yet).  
* **Shared packages used:** none.  
* **Modules affected:** `config-service` (F9), authentication (F4), LLM gateway cost-ceiling ledger (F5).  
* **Completion criteria:** instance reachable; migration tooling runs a no-op migration successfully in CI.

#### **F4 — Authentication Foundation**

* **Owner:** Foundation pod / Auth sub-lead  
* **Purpose:** Provision WorkOS tenant handling and ship a stub auth check, deferring live SSO/SCIM configuration to first design-partner onboarding.  
* **Dependencies:** F3 (session/tenant state storage).  
* **Outputs:** a provisioned WorkOS tenant; a stub auth-check middleware in `services/api`.  
* **Consumes:** F3's relational store for session state.  
* **Produces:** no live sessions yet (stub accepts a fixed test identity).  
* **Shared packages used:** none.  
* **Modules affected:** the API service (foundation-layer), and transitively every module behind it.  
* **Completion criteria:** WorkOS tenant exists; stub auth check exposes the exact interface the live check will implement; live SSO/SCIM explicitly marked staged, not attempted.

#### **F5 — LLM Gateway Foundation**

* **Owner:** Foundation pod / Gateway sub-lead  
* **Purpose:** Stand up the sole path from any module to any model provider, hardened against the March 2026 LiteLLM supply-chain incident, with a per-tenant cost-ceiling scaffold.  
* **Dependencies:** F3 (cost-ledger storage).  
* **Outputs:** a self-hosted LiteLLM deployment, installed from a pinned, signed, immutable tag with cosign signature verification as a CI step (Implementation Rule A7); `packages/llm-gateway-client`; a stubbed per-tenant cost-ceiling config with fail-closed behavior defined (Principle #23).  
* **Consumes:** F3's relational store for cost-ledger persistence.  
* **Produces:** cost/usage telemetry events (schema only; no real spend yet).  
* **Shared packages used:** none.  
* **Modules affected:** every LLM-driven module (1, 2, 3, 5, 6, 8) — hard rule: no module may call a model provider directly (Principle #1), enforced via lint-blocked raw SDK imports outside this package (Implementation Rule A5).  
* **Completion criteria:** LiteLLM image signature verified in CI, not manually; fail-closed mid-chain-exhaustion behavior implemented and unit-tested; named alert owner recorded.

#### **F6 — Orchestration Skeleton**

* **Owner:** Foundation pod / Orchestration sub-lead  
* **Purpose:** Stand up the checkpointed reasoning-chain skeleton with no module logic wired in yet, and scaffold (not activate) the durable-execution layer.  
* **Dependencies:** none.  
* **Outputs:** a LangGraph 1.2.x skeleton in `services/orchestrator`; an empty Temporal deployment manifest in `infra/temporal/`, provisioned but not deployed, behind a feature flag.  
* **Consumes:** nothing yet.  
* **Produces:** empty checkpointed state (no real steps).  
* **Shared packages used:** none.  
* **Modules affected:** Modules 1–6, 8 (all orchestrated steps, wired in their own sprints).  
* **Completion criteria:** skeleton runs a no-op chain end to end with checkpointing observable; confirmed no code path imports the deprecated `langgraph.prebuilt` module (targets `langchain.agents` instead, per Implementation Audit Technology Audit).

#### **F7 — Evaluation & Prompt Framework Foundation**

* **Owner:** Foundation pod / Eval sub-lead  
* **Purpose:** Wire DeepEval, RAGAS, and Promptfoo into CI as an empty gate, and establish the paired `prompts/module-XX` \+ `evals/module-XX` folder convention every module's DSPy work will fill in later.  
* **Dependencies:** none.  
* **Outputs:** CI jobs for DeepEval/RAGAS/Promptfoo; empty `prompts/` and `evals/` folder trees mirroring `modules/`; Langfuse Prompt Management wired for versioned prompt storage.  
* **Consumes:** nothing yet.  
* **Produces:** no real eval results yet.  
* **Shared packages used:** none.  
* **Modules affected:** every LLM-driven module (1, 2, 3, 5, 6, 8) attaches its own eval dataset in its own sprint.  
* **Completion criteria:** CI fails a deliberately-broken dummy prompt change and passes a correct one, proving the gate is live before any real prompt exists.

#### **F8 — Schema & Codegen Toolchain**

* **Owner:** Foundation pod / Schema sub-lead  
* **Purpose:** Establish the canonical-types-once, generated-everywhere pattern, using the corrected toolchain direction, and build the schema compatibility-check harness mechanism.  
* **Dependencies:** none.  
* **Outputs:** `packages/schemas` scaffold (empty, pattern only); a CI-wired codegen pipeline (Pydantic `.model_json_schema()` → `quicktype` → TypeScript — **not** `datamodel-code-generator`, per Implementation Audit's toolchain correction); `datamodel-code-generator` retained separately for Module 10's OpenAPI-to-Pydantic connector-model generation; the schema compatibility-check harness (unexercised until Sprint 2).  
* **Consumes:** nothing yet.  
* **Produces:** no entities yet.  
* **Shared packages used:** none.  
* **Modules affected:** every module and service that imports `packages/schemas` (all of them).  
* **Completion criteria:** a dummy Pydantic model change regenerates matching TypeScript in the same CI run automatically; the compatibility-check harness runs (against an empty schema) without erroring.

#### **F9 — Configuration Service Scaffold**

* **Owner:** Foundation pod / Config sub-lead  
* **Purpose:** Stand up versioned, tenant-overridable configuration plumbing for values expected to be calibrated later, without supplying any calibrated value yet.  
* **Dependencies:** F3 (relational storage for versioned config).  
* **Outputs:** `packages/config-service`.  
* **Consumes:** F3's relational store.  
* **Produces:** no live config values yet (schema and versioning mechanism only).  
* **Shared packages used:** none.  
* **Modules affected:** Modules 2 and 5 (calibrated values, Sprints 4 and 7); the LLM gateway (per-module routing table, F5).  
* **Completion criteria:** a dummy config value can be set, versioned, and tenant-overridden with a full change history, before any real calibrated value exists.

#### **F10 — Observability & Logging Foundation**

* **Owner:** Foundation pod / Observability sub-lead  
* **Purpose:** Instrument every service through one vendor-neutral standard, and stand up managed (not yet self-hosted) LLM tracing appropriate to synthetic-data-only internal build work.  
* **Dependencies:** none.  
* **Outputs:** OpenTelemetry instrumentation baseline across every service; `structlog` wired for application logging; managed Langfuse Cloud (or plain OpenTelemetry export) for LLM tracing.  
* **Consumes:** nothing yet.  
* **Produces:** trace and log data for every subsequent Epic's own testing.  
* **Shared packages used:** none.  
* **Modules affected:** every service and module (cross-cutting).  
* **Completion criteria:** a synthetic request through the orchestration skeleton (F6) produces a visible, correlated trace across API → orchestrator → gateway; self-hosted Langfuse explicitly deferred, not attempted, per its named trigger.

#### **F11 — Object Storage & Backup/DR**

* **Owner:** Foundation pod / Storage sub-lead  
* **Purpose:** Stand up object storage for large execution-trace artifacts with a retention window and a backup/DR policy attached from the first write — not after a cost or loss incident.  
* **Dependencies:** none.  
* **Outputs:** S3-compatible (or Cloudflare R2) bucket(s); a flat retention-window policy; a backup/DR policy covering both object storage and the graph substrate (coordinated with F2).  
* **Consumes:** nothing yet.  
* **Produces:** no real artifacts yet.  
* **Shared packages used:** none.  
* **Modules affected:** Module 4 (trace archives, Sprint 6) primarily.  
* **Completion criteria:** a test artifact write triggers a verifiable backup; a documented recovery drill succeeds against a deliberately-corrupted test write.

#### **F12 — Security Foundation**

* **Owner:** Foundation pod / Security sub-lead  
* **Purpose:** Produce a named threat model for the ingestion → action path (ticket/PR text ultimately driving Slack messages, Check Runs, generated test content) and a portable red-team scenario set, before Module 1 is exposed to real ticket content.  
* **Dependencies:** F1 (the ingestion path the threat model targets).  
* **Outputs:** a written indirect-prompt-injection threat model; a red-team scenario set authored as portable test data (not Promptfoo-specific pipeline logic, per Implementation Rule A8, hedging Promptfoo's post-acquisition ownership-change risk).  
* **Consumes:** F1's contract shape (to model the actual data path).  
* **Produces:** no live mitigations yet — mitigations are Phase 2+ security-engineering work per the Freeze's own Deferred Decisions.  
* **Shared packages used:** F7's eval/red-team CI wiring (to run the scenarios against, once modules exist to target).  
* **Modules affected:** Modules 1, 4, 6, 10 (the named ingestion→action path).  
* **Completion criteria:** threat model document exists and is reviewed; scenario set runs (as inert test data) against the Foundation skeleton without erroring; a standing watch item is opened on Promptfoo's post-acquisition roadmap with DeepEval's native red-teaming named as the fallback.

#### **F13 — Operational Readiness**

* **Owner:** Foundation pod / Platform lead (integrates outputs of F1–F12)  
* **Purpose:** Name who gets paged, write the first debugging runbook, and lock down monorepo dependency-management discipline before any module sprint begins.  
* **Dependencies:** soft dependency on F1–F12 (documents their outputs as they land; starts as a living skeleton on day one, finalized at Sprint 0 exit).  
* **Outputs:** a named, rotating on-call assignment for all seven foundation-layer services (Principle #22); a v0 debugging runbook correlating Langfuse, the Neo4j browser, connector logs, and application logs; one lockfile per language workspace (`uv.lock` for Python, `pnpm-lock.yaml` for Node); a CI rule failing any PR touching `packages/schemas` without a regenerated, committed TypeScript output; a monorepo-wide protobuf ≥4.x pin.  
* **Consumes:** F2, F5, F6, F10's provisioning state (to write the runbook against real, not fictional, instrumentation).  
* **Produces:** no runtime data — process and policy artifacts.  
* **Shared packages used:** none directly; documents all of them.  
* **Modules affected:** cross-cutting (every foundation-layer service).  
* **Completion criteria:** on-call rotation has a named first pager-holder; runbook exists and references real, live instrumentation (not placeholder text); both lockfiles are committed and CI-enforced.

#### **F14 — Frontend & Design System Scaffold *(Module 9 continuous track, origin)***

* **Owner:** Module 9 team  
* **Purpose:** Stand up the Next.js/shadcn/Tailwind frontend shell the Command Center will incrementally fill in throughout every subsequent sprint.  
* **Dependencies:** F4 (stub auth, for session-aware shell routing).  
* **Outputs:** a Next.js (App Router) application shell; shadcn/ui \+ Tailwind component baseline (CLI version pinned per Implementation Audit's Technology Audit); TanStack Table/Query wiring; Recharts/visx wiring; a WebSocket/SSE channel stub.  
* **Consumes:** F4's stub auth for session handling.  
* **Produces:** no real dashboard views yet — an empty, role-agnostic shell.  
* **Shared packages used:** `packages/ui-components` (created here).  
* **Modules affected:** Module 9 (this is Module 9's own Sprint-0 epic); every module's future dashboard surface builds on this shell.  
* **Completion criteria:** the shell renders, authenticates against the stub check, and can display the Sprint 0 demo milestone's raw trace entry (see Part 2).

## **Sprint 1 — Module 10 Epics**

#### **M10.1 — Jira Cloud Adapter**

* **Owner:** Module 10 team / Jira sub-lead  
* **Purpose:** Thin adapter translating Jira Cloud tickets into internal Requirement-shaped events.  
* **Dependencies:** F1 (contract), F4 (stored external-tool credentials).  
* **Outputs:** `services/connectors/jira/`.  
* **Consumes:** `packages/connector-contract`; Jira Cloud API.  
* **Produces:** normalized ingestion events (translation only, never interpretation).  
* **Shared packages used:** `connector-contract`.  
* **Modules affected:** Module 1 (ingestion consumer, Sprint 3).  
* **Completion criteria:** a real Jira ticket round-trips through the adapter and produces a contract-shaped event, verified in the Sprint 1 demo milestone.

#### **M10.2 — GitHub Adapter**

* **Owner:** Module 10 team / GitHub sub-lead  
* **Purpose:** Thin adapter for PR/diff events and posting advisory Check Runs back.  
* **Dependencies:** F1, F4.  
* **Outputs:** `services/connectors/github/`.  
* **Consumes:** `packages/connector-contract`; GitHub API.  
* **Produces:** normalized diff/event data; posted Check Run status (used later by Module 6, Sprint 8).  
* **Shared packages used:** `connector-contract`.  
* **Modules affected:** Module 2 (diff consumer, Sprint 4); Module 6 (Check Run poster, Sprint 8).  
* **Completion criteria:** a real PR event round-trips; a test Check Run posts successfully as advisory-only.

#### **M10.3 — Slack Adapter**

* **Owner:** Module 10 team / Slack sub-lead  
* **Purpose:** Thin adapter for posting status and notifications.  
* **Dependencies:** F1, F4.  
* **Outputs:** `services/connectors/slack/`.  
* **Consumes:** `packages/connector-contract`; Slack API.  
* **Produces:** posted messages (status/notification only).  
* **Shared packages used:** `connector-contract`.  
* **Modules affected:** any module posting human-facing notifications (primarily 6, 9).  
* **Completion criteria:** a test message posts successfully through the adapter.

#### **M10.4 — Playwright Adapter**

* **Owner:** Module 10 team / Playwright sub-lead  
* **Purpose:** Thin adapter executing the approved test suite against the fixed demo app.  
* **Dependencies:** F1.  
* **Outputs:** `services/connectors/playwright/`.  
* **Consumes:** `packages/connector-contract`.  
* **Produces:** raw execution results (translation only; Module 4 owns interpretation).  
* **Shared packages used:** `connector-contract`.  
* **Modules affected:** Module 4 (execution consumer, Sprint 6).  
* **Completion criteria:** a sample suite executes against the fixed demo app and returns raw pass/fail data through the contract.

#### **M10.5 — Legacy Adapter Contract-Test Fake**

* **Owner:** Module 10 team  
* **Purpose:** Prove the contract generalizes to a second execution target class without writing real Selenium/Appium/BrowserStack code (Accepted Change #19).  
* **Dependencies:** F1.  
* **Outputs:** a fake adapter, in the contract's own test suite only, under `services/connectors/legacy/`.  
* **Consumes:** `packages/connector-contract`.  
* **Produces:** no real execution data.  
* **Shared packages used:** `connector-contract`.  
* **Modules affected:** none directly — this is a contract-generality proof, not a shipped capability.  
* **Completion criteria:** the fake passes the same generic contract test suite as the four real adapters, with zero real Selenium/Appium/BrowserStack code present.

#### **M10.6 — Connector OpenAPI→Pydantic Codegen Wiring**

* **Owner:** Module 10 team  
* **Purpose:** Generate request/response Pydantic models from the Jira/GitHub/Slack OpenAPI specs, using `datamodel-code-generator` in the direction it actually supports (Implementation Audit toolchain correction).  
* **Dependencies:** F8 (schema toolchain), M10.1–M10.3.  
* **Outputs:** generated Pydantic models per adapter, checked into each adapter's own subfolder.  
* **Consumes:** each tool's public OpenAPI spec; `datamodel-code-generator`.  
* **Produces:** no runtime data — build-time models only.  
* **Shared packages used:** none (adapter-local generated models, not `packages/schemas`).  
* **Modules affected:** Module 10 only.  
* **Completion criteria:** regenerating from a spec change produces a clean diff with no manual patching required.

*(Module 9 continuous-track epic for this sprint: see M9.T1 below, Part 3 continuous-track summary.)*

## **Sprint 2 — Module 7 (Substrate) Epics**

#### **M7S.1 — Ten-Entity Schema Authoring**

* **Owner:** Module 7 team  
* **Purpose:** Author the frozen ten-entity schema as canonical Pydantic types, including the Waived/Accepted Defect \+ Rationale attribute, as the first schema element built under the new migration discipline.  
* **Dependencies:** F8 (schema/codegen toolchain pattern).  
* **Outputs:** ten entity type definitions in `packages/schemas` (Requirement, Test Case, Observation/Execution Result, Defect Report, ADR, Internal Go/No-Go Document, Triage/Strategy Decision Record, Production Incident/Post-Mortem, Risk Assessment Record, Historical Failure Pattern-lite), each additive-only from this point forward.  
* **Consumes:** F8's codegen pipeline.  
* **Produces:** the canonical schema TypeScript/Python types every other Epic imports from here forward.  
* **Shared packages used:** `packages/schemas`.  
* **Modules affected:** all ten modules (schema consumers).  
* **Completion criteria:** all ten entities compile, generate matching TypeScript, and pass the compatibility-check harness (M7S.3) as a merge gate.

#### **M7S.2 — `kg-client` Real Implementation \+ Tenant Scoping Enforcement**

* **Owner:** Module 7 team  
* **Purpose:** Swap Foundation's stub `kg-client` for a real, Neo4j-backed client that is the sole permitted Cypher query path, with mandatory `tenant_id` filtering on every query.  
* **Dependencies:** F2 (Neo4j instance \+ stub interface), M7S.1 (schema to query against).  
* **Outputs:** a production `kg-client` implementation, same public interface as F2's stub.  
* **Consumes:** F2's Neo4j instance; M7S.1's entity types.  
* **Produces:** real, tenant-scoped graph reads/writes.  
* **Shared packages used:** `packages/kg-client`, `packages/schemas`.  
* **Modules affected:** all graph-touching modules (1, 2, 5, 6, 7, 8).  
* **Completion criteria:** per ADR-011 — a missed-filter test provably cannot leak a second tenant's data; no other code path in the repository issues a raw Cypher query (enforced by lint/CI, not convention).

#### **M7S.3 — Schema Compatibility-Check Harness, First Exercise**

* **Owner:** Module 7 team  
* **Purpose:** Exercise the Foundation-built harness mechanism (F8) against the first real schema, establishing it as a live merge gate rather than an unexercised mechanism.  
* **Dependencies:** F8 (harness mechanism), M7S.1 (real schema to check).  
* **Outputs:** a passing CI run of the compatibility-check harness against the ten-entity schema.  
* **Consumes:** F8's harness; M7S.1's schema.  
* **Produces:** no runtime data — a CI artifact (pass/fail gate).  
* **Shared packages used:** `packages/schemas`.  
* **Modules affected:** every future schema-touching Epic in every subsequent sprint.  
* **Completion criteria:** a deliberately-breaking schema change (a rename without a deprecation window) is caught and blocked in CI; an additive change passes.

#### **M7S.4 — LightRAG-Style Construction Wiring**

* **Owner:** Module 7 team  
* **Purpose:** Wire lightweight graph construction for V1, pinned to a post-refactor `lightrag-hku` release.  
* **Dependencies:** M7S.2 (real graph to construct into).  
* **Outputs:** a construction pipeline wired into the graph-service.  
* **Consumes:** `kg-client`; `lightrag-hku` (pinned per Implementation Audit).  
* **Produces:** constructed graph structure from ingested entities.  
* **Shared packages used:** `packages/kg-client`.  
* **Modules affected:** Module 7 surface (Sprint 9, consumes construction quality).  
* **Completion criteria:** a synthetic entity set constructs correctly and is retrievable via the graph service's native hybrid/vector search.

#### **M7S.5 — Shared Trust/Confidence Indicator Schema**

* **Owner:** Module 7 team (schema authority)  
* **Purpose:** Decide, once, the shared shape every confidence/trust/acceptance-emitting module (at minimum 2, 3, 5) will use — before Module 2's sprint needs it, per Implementation Audit Rule A11.  
* **Dependencies:** F8 (codegen pipeline), M7S.1 (co-located schema work).  
* **Outputs:** one shared trust-indicator Pydantic type in `packages/schemas`.  
* **Consumes:** F8's pipeline.  
* **Produces:** the shape every future confidence-emitting Epic (M2.1, M3.1, M5.1) will populate.  
* **Shared packages used:** `packages/schemas`.  
* **Modules affected:** Modules 2, 3, 5 (producers); Module 9 (consumer, displays each separately — Part 3 IH.1).  
* **Completion criteria:** the type is reviewed and frozen before Sprint 4 (Module 2) begins its own Epics.

#### **SI.1 — Rendering/Citation Service Scaffold**

* **Owner:** Shared Infrastructure pod (distinct from the Module 7 team)  
* **Purpose:** Build the one "structured, cited entities → trustworthy human artifact" transformation, early and once, against the now-defined ten-entity schema.  
* **Dependencies:** M7S.1 (entity shapes to render).  
* **Outputs:** `packages/rendering` v0 (initial template/transformation scaffold).  
* **Consumes:** M7S.1's entity types.  
* **Produces:** rendered artifact stubs (no real business content yet).  
* **Shared packages used:** `packages/schemas`.  
* **Modules affected:** Module 6 (Sprint 8, go/no-go brief); Module 9 (continuous, every dashboard surface); Module 7 surface (Sprint 9, cited answers).  
* **Completion criteria:** a synthetic entity renders into a human-readable artifact with a traceable citation link.

*(Module 9 continuous-track epic for this sprint: see M9.T2 below.)*

## **Sprint 3 — Module 1 Epics**

#### **M1.0a — Claude Agent SDK Scoping Decision**

* **Owner:** Platform / AI Engineering lead  
* **Purpose:** Resolve, explicitly and before Module 1's build begins, whether Modules 1/2/5 use Claude Agent SDK with its tool surface reduced to zero built-in tools plus narrow custom in-process MCP tools, or drop it entirely in favor of direct Anthropic API calls through `packages/extraction` and `packages/llm-gateway-client` (Implementation Audit AI Engineering Audit; Engineering Risk #3).  
* **Dependencies:** F5 (LLM gateway), F7 (eval framework).  
* **Outputs:** a recorded scoping decision (option a or b), applied identically across Modules 1, 2, 5.  
* **Consumes:** nothing (a decision Epic, not a code Epic).  
* **Produces:** no runtime data.  
* **Shared packages used:** `packages/llm-gateway-client`, `packages/extraction`.  
* **Modules affected:** Modules 1, 2, 5 (all three inherit this decision — it is made once, here, not three times).  
* **Completion criteria:** decision recorded with reasoning, before M1.1 begins; Implementation Rule A6 satisfied (Claude Agent SDK is not used in any V1 module's business logic until this decision is made explicitly).

#### **M1.0b — Module 1 ↔ Module 3 Boundary Contract**

* **Owner:** Module 1 lead \+ Module 3 lead, jointly, arbitrated by Platform  
* **Purpose:** Encode where "ambiguity detection" ends and "boundary-condition test design" begins as an explicit Pydantic contract, resolving Moderate Concern #1 before either module's implementation session starts (Modularity Audit, Exception 2).  
* **Dependencies:** F8 (schema toolchain), M7S.1 (entity shapes the contract references).  
* **Outputs:** a boundary-contract Pydantic type in `packages/schemas`.  
* **Consumes:** M7S.1's Requirement/Risk entity shapes.  
* **Produces:** the shared shape M1.1 and (later) M3.1 will both honor.  
* **Shared packages used:** `packages/schemas`.  
* **Modules affected:** Module 1 (this sprint); Module 3 (Sprint 5 — receives this contract already frozen).  
* **Completion criteria:** the validation spike concludes and the resulting boundary is a compiled Pydantic type, not a paragraph in a design doc, before M1.1 begins.

#### **M1.1 — Ambiguity/Gap Taxonomy \+ DSPy Signature**

* **Owner:** Module 1 team  
* **Purpose:** Implement the core extraction logic — identify implicit gaps against a versioned, evidence-based taxonomy; draft clarifying questions and acceptance criteria.  
* **Dependencies:** M1.0a (Agent SDK decision), M1.0b (boundary contract), F7 (eval framework).  
* **Outputs:** Module 1's DSPy signature and rubric-scored taxonomy logic in `modules/module-01-requirement-intelligence/`.  
* **Consumes:** `packages/extraction`, `packages/llm-gateway-client`, `kg-client`.  
* **Produces:** clarifying questions and draft acceptance criteria (written back to the Requirement entity in M1.2).  
* **Shared packages used:** `extraction`, `llm-gateway-client`, `kg-client`, DSPy.  
* **Modules affected:** Module 1 only (this is its core logic).  
* **Completion criteria:** given one realistic Jira ticket, produces clarifying questions and draft acceptance criteria from a visibly-fired checklist item.

#### **M1.2 — Requirement Ingestion Wiring**

* **Owner:** Module 1 team  
* **Purpose:** Wire the connector-layer-to-graph-write path for the Requirement entity.  
* **Dependencies:** M10.1 (Jira adapter), M7S.2 (real `kg-client`).  
* **Outputs:** an ingestion handler in `modules/module-01-requirement-intelligence/`.  
* **Consumes:** Module 10's normalized ingestion events; `kg-client`.  
* **Produces:** persisted Requirement entities.  
* **Shared packages used:** `kg-client`.  
* **Modules affected:** Module 1 only.  
* **Completion criteria:** an ingested Jira ticket is persisted as a Requirement entity, human-reviewable before validation, with no auto-commit path.

#### **M1.3 — Module 1 Eval Dataset \+ DSPy Compiled-Artifact Versioning**

* **Owner:** Module 1 team  
* **Purpose:** Attach an evaluation dataset from Module 1's first working version, and commit its DSPy-compiled program state as a distinct, versioned artifact from the source signature (Implementation Rule A4).  
* **Dependencies:** M1.1, F7.  
* **Outputs:** `evals/module-01/` dataset; a committed compiled-program artifact alongside the source signature.  
* **Consumes:** F7's CI wiring.  
* **Produces:** eval pass/fail results.  
* **Shared packages used:** DeepEval/RAGAS/Promptfoo harness.  
* **Modules affected:** Module 1 only.  
* **Completion criteria:** no prompt change (or DSPy/LangGraph version bump, per Implementation Rule A3) merges without this suite passing; the compiled program's serialized state is a reviewable diff, not an invisible side effect of re-running the optimizer.

## **Sprint 4 — Module 2 Epics**

#### **M2.1 — Risk Exposure Scoring Logic \+ DSPy Signature**

* **Owner:** Module 2 team  
* **Purpose:** Assess Change Surface, Historical Defect Density, and Business Criticality into a Risk Exposure Score with a stated rationale.  
* **Dependencies:** M1.0a (inherited Agent SDK decision), M7S.5 (trust-indicator schema).  
* **Outputs:** Module 2's DSPy signature in `modules/module-02-risk-strategy/`.  
* **Consumes:** `packages/extraction`, `llm-gateway-client`, `kg-client`, M10.2's diff events.  
* **Produces:** a Risk Assessment Record with Stated Rationale, emitting the shared trust-indicator shape.  
* **Shared packages used:** `extraction`, `llm-gateway-client`, `kg-client`, `schemas` (trust indicator), DSPy.  
* **Modules affected:** Module 2 only.  
* **Completion criteria:** produces a Risk Assessment Record plus a rationale sentence citing an actual graph-sourced number.

#### **M2.2 — Calibration Process Definition (Risk-to-Coverage Heuristic)**

* **Owner:** Module 2 team \+ design-partner QA lead  
* **Purpose:** Define the process — not the value — that will calibrate the risk-to-coverage heuristic: a named calibration-session owner, a minimum sample size before "calibrated" replaces "provisional," and a documented disagreement tie-break rule (Accepted Change #6).  
* **Dependencies:** F9 (config-service scaffold).  
* **Outputs:** a documented calibration process, recorded in `config-service`'s metadata for this value.  
* **Consumes:** F9's versioning mechanism.  
* **Produces:** no calibrated value yet — the process only.  
* **Shared packages used:** `packages/config-service`.  
* **Modules affected:** Module 2 only (Module 5's analogous process is Epic M5.3, its own Epic, not this one).  
* **Completion criteria:** owner named, minimum sample size stated, disagreement rule documented — before this sprint is called complete (not before it starts).

#### **M2.3 — Historical Defect Density Graph Query Path**

* **Owner:** Module 2 team  
* **Purpose:** Read a graph-resident view of historical defect density to ground the risk score in real data.  
* **Dependencies:** M7S.2 (real `kg-client`).  
* **Outputs:** a query path in `modules/module-02-risk-strategy/`.  
* **Consumes:** `kg-client`.  
* **Produces:** no new entities — a read path only.  
* **Shared packages used:** `kg-client`.  
* **Modules affected:** Module 2 only.  
* **Completion criteria:** returns a real, non-fixture historical-density number for at least one synthetic component.

#### **M2.4 — Module 2 Eval Dataset \+ Config-Service Wiring**

* **Owner:** Module 2 team  
* **Purpose:** Attach Module 2's eval dataset and wire the heuristic into `config-service` as a swappable value, never a hard-coded constant.  
* **Dependencies:** M2.1, F7, F9.  
* **Outputs:** `evals/module-02/`; a config-backed heuristic value.  
* **Consumes:** F7's CI wiring; F9's config plumbing.  
* **Produces:** eval pass/fail results.  
* **Shared packages used:** eval harness, `config-service`.  
* **Modules affected:** Module 2 only.  
* **Completion criteria:** the heuristic is swappable via config without a redeploy; eval suite gates every future change to it.

## **Sprint 5 — Module 3 Epics**

#### **M3.1 — Test Case Generation Logic**

* **Owner:** Module 3 team  
* **Purpose:** Generate functional, boundary, and negative test cases against the frozen Module 1/3 boundary contract (M1.0b).  
* **Dependencies:** M1.0b (boundary contract), M2.1 (Risk Assessment Record to consume), M7S.5 (trust-indicator schema).  
* **Outputs:** generation logic in `modules/module-03-test-generation/`.  
* **Consumes:** the Requirement and Risk Assessment Record via `kg-client`; `packages/extraction`.  
* **Produces:** candidate test cases, tagged distinctly from human-authored ones (Principle #9), emitting the trust-indicator shape.  
* **Shared packages used:** `extraction`, `kg-client`, `schemas`.  
* **Modules affected:** Module 3 only.  
* **Completion criteria:** generates a candidate set from a real Requirement \+ Risk Assessment Record pair.

#### **M3.2 — Mutation-Testing Feedback Loop**

* **Owner:** Module 3 team  
* **Purpose:** Run the generate → mutate → discard → review loop against Stryker, matching the demo app's assumed JS/TS language.  
* **Dependencies:** M3.1.  
* **Outputs:** Stryker 9.6.x CI wiring in `mutation-testing/`.  
* **Consumes:** M3.1's candidate test cases; the fixed demo app's source.  
* **Produces:** mutation scores per candidate.  
* **Shared packages used:** none (mutation-testing is its own top-level folder, not a `packages/` import).  
* **Modules affected:** Module 3 only.  
* **Completion criteria:** at least one real mutation-testing pass runs against the fixed demo app and produces a mutation score.

#### **M3.3 — Human Review/Approval Surface Backend**

* **Owner:** Module 3 team  
* **Purpose:** Persist only human-approved Test Case entities; discarded generations are never silently kept as approved.  
* **Dependencies:** M3.1, M3.2.  
* **Outputs:** an approval-gated write path in `modules/module-03-test-generation/`.  
* **Consumes:** `kg-client`.  
* **Produces:** approved Test Case entities only.  
* **Shared packages used:** `kg-client`.  
* **Modules affected:** Module 3 only.  
* **Completion criteria:** no auto-commit path exists; a rejected candidate is provably never persisted as a Test Case entity.

#### **M3.4 — Module 3 Eval Dataset \+ Mutation-Score Baseline**

* **Owner:** Module 3 team  
* **Purpose:** Attach Module 3's eval dataset and record a mutation-score baseline against the documented \~30–41% ceiling.  
* **Dependencies:** M3.2, F7.  
* **Outputs:** `evals/module-03/`; a recorded baseline mutation score.  
* **Consumes:** F7's CI wiring.  
* **Produces:** eval and mutation-score results.  
* **Shared packages used:** eval harness.  
* **Modules affected:** Module 3 only.  
* **Completion criteria:** baseline recorded; no prompt or engine-version change merges without both eval and mutation gates passing.

## **Sprint 6 — Module 4 Epics**

#### **M4.1 — Suite Trigger \+ Playwright Execution Wiring**

* **Owner:** Module 4 team  
* **Purpose:** Trigger the approved test suite via Module 10's Playwright adapter.  
* **Dependencies:** M3.3 (approved Test Case entities), M10.4 (Playwright adapter).  
* **Outputs:** trigger logic in `modules/module-04-execution-orchestration/`.  
* **Consumes:** `connector-contract`; approved Test Case entities via `kg-client`.  
* **Produces:** execution trigger events.  
* **Shared packages used:** `connector-contract`, `kg-client`.  
* **Modules affected:** Module 4 only.  
* **Completion criteria:** an approved suite triggers and runs live against the fixed demo app.

#### **M4.2 — Observation/Execution Result Persistence**

* **Owner:** Module 4 team  
* **Purpose:** Persist execution results without corrupting or silently losing an in-flight result on crash.  
* **Dependencies:** M4.1, F11 (object storage for trace artifacts).  
* **Outputs:** a persistence path in `modules/module-04-execution-orchestration/`.  
* **Consumes:** raw execution data from the Playwright adapter; object storage (F11); `kg-client`.  
* **Produces:** Observation/Execution Result entities plus archived trace artifacts.  
* **Shared packages used:** `kg-client`, object storage client.  
* **Modules affected:** Module 4 only; Module 5 (Sprint 7, consumes failing results).  
* **Completion criteria:** a crash mid-execution does not corrupt or lose the in-flight result (tested via deliberate fault injection).

#### **M4.3 — Self-Verification State-Machine Gate**

* **Owner:** Module 4 team  
* **Purpose:** Enforce, structurally, that a module's own test result is never the sole gate on its own related fix — independent of whether Temporal is active (Principle #7).  
* **Dependencies:** M4.2, F6 (LangGraph skeleton).  
* **Outputs:** an orchestration state-machine rule in `services/orchestrator/`.  
* **Consumes:** LangGraph's checkpointing.  
* **Produces:** gate-pass/gate-fail decisions on execution results.  
* **Shared packages used:** none (orchestration-layer logic).  
* **Modules affected:** Module 4 (this sprint); every module whose output could otherwise self-verify.  
* **Completion criteria:** a deliberately-crafted "self-verifying" test case is demonstrably rejected by the gate.

#### **M4.4 — Temporal Scaffold Behind Feature Flag**

* **Owner:** Module 4 team \+ Platform  
* **Purpose:** Provision (not activate) the durable-execution layer, per its named staged trigger, using the official `temporalio[langgraph]` integration extra rather than hand-rolled glue (Implementation Audit positive finding).  
* **Dependencies:** F6 (Temporal manifest placeholder).  
* **Outputs:** an inactive Temporal deployment behind a feature flag in `infra/temporal/`.  
* **Consumes:** `temporalio[langgraph]`.  
* **Produces:** no active workflows — provisioned readiness only.  
* **Shared packages used:** none.  
* **Modules affected:** Module 4 (readiness task only — not a deployment task, per the Freeze's own staged-adoption instruction).  
* **Completion criteria:** the feature flag toggles the layer on in a test environment without code changes, proving readiness without activating it in production.

*(Module 9 continuous-track epics for Sprints 3–6: see M9.T3–M9.T6 below.)*

## **Sprint 7 — Module 5 Epics**

#### **M5.0 — Fixture-Backed Fake Graph-Context Provider**

* **Owner:** Module 5 team  
* **Purpose:** Decouple Module 5's build/eval timeline from Module 7's still-unbuilt product surface, by extending the Foundation-boundary stub-and-swap pattern one level up (Implementation Audit Modularity Audit, Exception 1; Implementation Rule A10).  
* **Dependencies:** M7S.2 (real substrate exists; surface does not yet).  
* **Outputs:** a fixture-backed fake graph-context provider (synthetic execution history, environment telemetry, prior-similar-failure records) in `modules/module-05-defect-triage/`.  
* **Consumes:** nothing live — synthetic fixtures only.  
* **Produces:** fake context for M5.1's classification logic to develop and eval-test against.  
* **Shared packages used:** none (module-local fixture).  
* **Modules affected:** Module 5 only.  
* **Completion criteria:** M5.1 passes its eval suite against this fake provider before the real retrieval path (M5.4) is validated — Module 5's calendar slot never silently depends on Module 7 finishing well.

#### **M5.1 — Reproducibility Judgment \+ Defect-vs-Flake Classification Logic**

* **Owner:** Module 5 team  
* **Purpose:** Query graph context (never the failure log alone) to produce a reproducibility judgment, a defect-vs-flake classification with a calibrated confidence score, and a business-severity call.  
* **Dependencies:** M5.0 (fake context to build against), M1.0a (inherited Agent SDK decision), M7S.5 (trust-indicator schema).  
* **Outputs:** Module 5's DSPy signature in `modules/module-05-defect-triage/`.  
* **Consumes:** `packages/extraction`, `llm-gateway-client`, M5.0's fake context (later M5.4's real context).  
* **Produces:** a Defect Report entity draft, emitting the trust-indicator shape.  
* **Shared packages used:** `extraction`, `llm-gateway-client`, `schemas`.  
* **Modules affected:** Module 5 only.  
* **Completion criteria:** on a failing Observation/Execution Result, produces a reproducibility judgment and a confidence-scored defect-vs-flake call.

#### **M5.2 — Waived/Accepted Defect \+ Rationale Attribute Wiring**

* **Owner:** Module 5 team  
* **Purpose:** Wire the schema attribute M7S.1 added, so a defect triaged as accepted risk (rather than blocking) carries a rationale.  
* **Dependencies:** M7S.1 (schema attribute), M5.1.  
* **Outputs:** a write path populating the attribute on the Defect Report entity.  
* **Consumes:** M7S.1's schema; `kg-client`.  
* **Produces:** Defect Report entities including the waived-defect attribute where applicable.  
* **Shared packages used:** `kg-client`, `schemas`.  
* **Modules affected:** Module 5 (this sprint); Module 6 (Sprint 8, consumes and surfaces this attribute).  
* **Completion criteria:** a waived defect visibly carries its rationale through to persistence, with no silent loss of that field.

#### **M5.3 — Calibration Process Definition (Escalation Confidence Threshold)**

* **Owner:** Module 5 team \+ design-partner QA lead  
* **Purpose:** Define the process — named owner, minimum sample size, disagreement rule — that will calibrate Module 5's escalation confidence threshold, mirroring M2.2's process for Module 2's heuristic (Accepted Change #6).  
* **Dependencies:** F9 (config-service).  
* **Outputs:** a documented calibration process for this value.  
* **Consumes:** F9's versioning mechanism.  
* **Produces:** no calibrated value yet — the process only.  
* **Shared packages used:** `packages/config-service`.  
* **Modules affected:** Module 5 only.  
* **Completion criteria:** owner named, minimum sample size stated, disagreement rule documented, before this sprint is called complete.

#### **M5.4 — Real Retrieval-Path Swap-In**

* **Owner:** Module 5 team  
* **Purpose:** Swap M5.0's fake graph-context provider for Module 7's real retrieval path once validated for Module 5's specific query patterns — not gated on Module 7's full product surface (Sprint 9).  
* **Dependencies:** M5.0, M5.1, M7S.4 (substrate retrieval/construction quality).  
* **Outputs:** a validated real-context provider replacing the fixture.  
* **Consumes:** `kg-client`; M7S.4's constructed graph.  
* **Produces:** real (not synthetic) reproducibility/classification judgments.  
* **Shared packages used:** `kg-client`.  
* **Modules affected:** Module 5 only.  
* **Completion criteria:** M5.1's eval suite passes identically against the real path as it did against the fake one, before this sprint is called complete.

#### **M5.5 — Module 5 Eval Dataset**

* **Owner:** Module 5 team  
* **Purpose:** Attach an evaluation dataset from Module 5's first working version.  
* **Dependencies:** M5.1, F7.  
* **Outputs:** `evals/module-05/`.  
* **Consumes:** F7's CI wiring.  
* **Produces:** eval pass/fail results.  
* **Shared packages used:** eval harness.  
* **Modules affected:** Module 5 only.  
* **Completion criteria:** no change to Module 5's classification logic, prompt, or a DSPy/LangGraph dependency bump merges without this suite passing.

## **Sprint 8 — Module 6 Epics**

#### **M6.1 — Go/No-Go Aggregation Logic**

* **Owner:** Module 6 team  
* **Purpose:** Aggregate the Risk Assessment Record, Test Case/Observation results, and open Defect Reports into a cited Internal Go/No-Go Document — advisory only, never an autonomous release trigger (Principle #14).  
* **Dependencies:** M2.1, M3.3, M5.2.  
* **Outputs:** aggregation logic in `modules/module-06-release-readiness/`.  
* **Consumes:** `kg-client` reads across three upstream entity types.  
* **Produces:** an Internal Go/No-Go Document entity, including the waived-defect attribute.  
* **Shared packages used:** `kg-client`.  
* **Modules affected:** Module 6 only.  
* **Completion criteria:** produces an aggregated, cited document from real upstream entities.

#### **M6.2 — Waived-Defect Rationale Surfacing**

* **Owner:** Module 6 team  
* **Purpose:** Make surfacing any aggregated waived-defect rationale a completion criterion, not an incidental side effect of the schema change (Freeze's changed Definition of Done for Module 6).  
* **Dependencies:** M6.1, M5.2.  
* **Outputs:** explicit rationale-surfacing logic in the aggregation output.  
* **Consumes:** M5.2's attribute.  
* **Produces:** a go/no-go brief that visibly displays waived-defect rationale.  
* **Shared packages used:** none beyond M6.1's own.  
* **Modules affected:** Module 6 only.  
* **Completion criteria:** a synthetic waived defect is visibly present in the rendered brief, not merely present in the underlying data.

#### **M6.3 — Rendering Integration \+ GitHub Check Run Posting**

* **Owner:** Module 6 team  
* **Purpose:** Render the aggregated document via the shared rendering service and post it as an advisory GitHub Check Run.  
* **Dependencies:** SI.1 (rendering service), M10.2 (GitHub adapter), M6.1.  
* **Outputs:** rendering \+ posting logic in `modules/module-06-release-readiness/`.  
* **Consumes:** `packages/rendering`; `connector-contract` (GitHub adapter).  
* **Produces:** a rendered artifact; a posted advisory Check Run.  
* **Shared packages used:** `rendering`, `connector-contract`.  
* **Modules affected:** Module 6 only; Module 9 (consumes the same rendered artifact for its Go/No-Go surface).  
* **Completion criteria:** a real Check Run posts as advisory, never blocking, on a test PR.

#### **M6.4 — Module 6 Eval Dataset**

* **Owner:** Module 6 team  
* **Purpose:** Attach an evaluation dataset from Module 6's first working version.  
* **Dependencies:** M6.1, F7.  
* **Outputs:** `evals/module-06/`.  
* **Consumes:** F7's CI wiring.  
* **Produces:** eval pass/fail results.  
* **Shared packages used:** eval harness.  
* **Modules affected:** Module 6 only.  
* **Completion criteria:** no aggregation-logic or template change merges without this suite passing.

## **Sprint 9 — Module 7 (Product Surface) Epics**

#### **M7P.1 — Text-to-Cypher Query Path**

* **Owner:** Module 7 team  
* **Purpose:** Answer a natural-language question by retrieving specific, relevant entities first — never fluent, unattributed prose.  
* **Dependencies:** M7S.2, M7S.4 (substrate and construction, populated with real multi-module data by this point in the build order).  
* **Outputs:** a Text-to-Cypher query path in `services/graph-service/`.  
* **Consumes:** `kg-client`; the constructed graph.  
* **Produces:** query results with a traceable link to the grounding entity.  
* **Shared packages used:** `kg-client`.  
* **Modules affected:** Module 7 only.  
* **Completion criteria:** a natural-language query matching the demo script returns specific, correctly-grounded entities.

#### **M7P.2 — Citation-Grounded Answer Rendering**

* **Owner:** Module 7 team  
* **Purpose:** Render Text-to-Cypher results as a cited answer via the shared rendering service, never unattributed prose.  
* **Dependencies:** M7P.1, SI.1 (rendering service).  
* **Outputs:** rendering integration in `services/graph-service/`.  
* **Consumes:** `packages/rendering`.  
* **Produces:** a cited, human-readable answer.  
* **Shared packages used:** `rendering`.  
* **Modules affected:** Module 7 only; Module 9 (Knowledge Query surface).  
* **Completion criteria:** every returned answer carries a citation to a specific entity ID.

#### **M7P.3 — Retrieval-Precision Baseline Capture**

* **Owner:** Module 7 team  
* **Purpose:** Capture a retrieval-precision baseline on Neo4j's native hybrid search alone, informing (not triggering) the still-staged reranker decision.  
* **Dependencies:** M7P.1.  
* **Outputs:** a recorded baseline metric.  
* **Consumes:** M7P.1's query results.  
* **Produces:** a precision baseline dataset.  
* **Shared packages used:** none.  
* **Modules affected:** Module 7 only; feeds the standing staged-adoption tracker (F13/IH.6).  
* **Completion criteria:** baseline recorded and reviewed; no reranker adopted preemptively against it (Demo Optimization #8, still correctly deferred).

#### **M7P.4 — Module 7 Surface Eval Dataset**

* **Owner:** Module 7 team  
* **Purpose:** Attach an evaluation dataset for the retrieval/citation surface specifically (distinct from the substrate's own schema tests).  
* **Dependencies:** M7P.1, F7.  
* **Outputs:** `evals/module-07-surface/`.  
* **Consumes:** F7's CI wiring.  
* **Produces:** eval pass/fail results.  
* **Shared packages used:** eval harness (RAGAS specifically, for retrieval metrics).  
* **Modules affected:** Module 7 only.  
* **Completion criteria:** no change to the query or citation path merges without this suite passing.

## **Sprint 10 — Module 8 Epics**

#### **M8.0 — Validation Spike / Go–No-Go Checkpoint *(gating epic)***

* **Owner:** Module 8 team \+ Platform lead  
* **Purpose:** Validate Module 8's core "AI-Augmented" capability classification before any build begins, with a real possible outcome of re-scoping to Human-Only (Accepted Change #9).  
* **Dependencies:** none beyond Sprint 9's completion (build-order position).  
* **Outputs:** a recorded spike outcome and reasoning.  
* **Consumes:** nothing — this is an evaluation of feasibility, not a code Epic.  
* **Produces:** no runtime data.  
* **Shared packages used:** none.  
* **Modules affected:** Module 8 only, but decisively — M8.1–M8.3 do not begin until this Epic completes.  
* **Completion criteria:** an explicit decision is recorded — proceed as AI-Augmented, or re-scope to Human-Only — as a scope conversation, not a mid-sprint surprise.

#### **M8.1 — Production Incident Capture**

* **Owner:** Module 8 team  
* **Purpose:** Capture a Production Incident entity via manual entry or a monitoring-integration hook.  
* **Dependencies:** M8.0 (cleared AI-Augmented), M7S.1 (entity schema).  
* **Outputs:** capture logic in `modules/module-08-feedback-learning-loop/`.  
* **Consumes:** `kg-client`.  
* **Produces:** Production Incident entities.  
* **Shared packages used:** `kg-client`, `schemas`.  
* **Modules affected:** Module 8 only.  
* **Completion criteria:** a manually-entered incident persists correctly as a Production Incident entity.

#### **M8.2 — Action-Item Extraction \+ Risk Assessment / Historical Failure Pattern Update**

* **Owner:** Module 8 team  
* **Purpose:** Extract action items from a captured incident and update the affected component's Risk Assessment Record and Historical Failure Pattern-lite counter — deliberately narrow, no auto-generation of new test cases or ADRs at V1.  
* **Dependencies:** M8.1, M1.1 (reused extraction pattern), M7S.2 (reused write path).  
* **Outputs:** extraction \+ update logic in `modules/module-08-feedback-learning-loop/`.  
* **Consumes:** `packages/extraction` (reused from Module 1); `kg-client` (reused write path from Module 7).  
* **Produces:** updated Risk Assessment Record and Historical Failure Pattern-lite entity.  
* **Shared packages used:** `extraction`, `kg-client`.  
* **Modules affected:** Module 8 (this sprint); Module 2 (consumes the updated density view on the next Requirement touching that component).  
* **Completion criteria:** a captured incident visibly updates the affected component's Risk Assessment Record, closing the loop concretely.

#### **M8.3 — Module 8 Eval Dataset**

* **Owner:** Module 8 team  
* **Purpose:** Attach an evaluation dataset from Module 8's first working version.  
* **Dependencies:** M8.2, F7.  
* **Outputs:** `evals/module-08/`.  
* **Consumes:** F7's CI wiring.  
* **Produces:** eval pass/fail results.  
* **Shared packages used:** eval harness.  
* **Modules affected:** Module 8 only.  
* **Completion criteria:** no extraction-logic change merges without this suite passing.

*(Module 9 continuous-track epics for Sprints 7–10: see M9.T7–M9.T10 below.)*

## **Module 9 — Continuous Track (Sprints 0–11)**

Per §1.1, Module 9 is not a pipeline stage and holds no dedicated sprint slot of its own. It is one small epic per sprint, listed here together for a single point of reference; each row is that sprint's Module 9 epic and is scheduled *inside* that sprint (Part 3 above already places M9.T0 as F14).

| Sprint | Epic | Owner | Purpose | Depends on (same sprint) | Completion criteria |
| ----- | ----- | ----- | ----- | ----- | ----- |
| 0 | M9.T0 (= F14) | Module 9 team | Frontend \+ design-system shell | F4 | Renders Sprint 0's raw-trace demo milestone |
| 1 | M9.T1 | Module 9 team | Command Center shell \+ real-event log view | M10.1–M10.4 | Displays a real ingested event from each of the four adapters |
| 2 | M9.T2 | Module 9 team | Live-trace stub wiring against the real substrate | M7S.2 | Displays a real, tenant-scoped entity read from the graph |
| 3 | M9.T3 | Module 9 team | Requirement review surface (human edit/approve UI) | M1.1, M1.2 | A human can edit and approve Module 1's output in the UI |
| 4 | M9.T4 | Module 9 team | Risk Assessment surface, first real use of the trust-indicator schema | M2.1, M7S.5 | Displays a Risk Assessment Record with its trust indicator shown separately |
| 5 | M9.T5 | Module 9 team | Test Case review surface | M3.3 | A human can approve/reject candidate test cases in the UI |
| 6 | M9.T6 | Module 9 team | Live execution streaming (progress bar / streaming channel) | M4.1 | Displays live progress of a real suite run |
| 7 | M9.T7 | Module 9 team | Defect Triage surface | M5.1, M5.2 | Displays a Defect Report including waived-defect rationale where present |
| 8 | M9.T8 | Module 9 team | Go/No-Go brief surface | M6.1, M6.3 | Displays the rendered, cited go/no-go brief |
| 9 | M9.T9 | Module 9 team | Knowledge Query surface | M7P.2 | A human can ask a natural-language question and see a cited answer |
| 10 | M9.T10 | Module 9 team | Feedback Loop surface | M8.1, M8.2 | Displays an incident's extracted action items and the resulting Risk Assessment update |
| 11 | IH.1 (final) | Module 9 team | Full hardening pass — see Sprint 11 below | all of the above | Role-aware views live; trust indicators shown separately, never blended |

## **Sprint 11 — Integration Hardening & Demo Readiness Epics**

#### **IH.1 — Module 9 Final Hardening Pass**

* **Owner:** Module 9 team  
* **Purpose:** Consolidate ten sprints of incremental dashboard work into the frozen Definition of Done: a minimum QA Engineer view and QA Lead view, live-streaming the full primary chain as one coherent, persisted history, with per-module trust/reliability indicators shown separately, never blended into one confidence number.  
* **Dependencies:** M9.T0–M9.T10 (every prior continuous-track epic).  
* **Outputs:** the finished Command Center.  
* **Consumes:** every module's real output, end to end.  
* **Produces:** no new entities — a presentation layer only.  
* **Shared packages used:** `rendering`, `ui-components`, the API service, the streaming channel.  
* **Modules affected:** Module 9 only, but it is the sprint's centerpiece deliverable.  
* **Completion criteria:** both required role views exist; per-module indicators (M7S.5's shared shape) are visually distinct, never combined into a single number.

#### **IH.2 — End-to-End Demo Rehearsal**

* **Owner:** Platform / Engineering Manager  
* **Purpose:** Run the full primary eight-step chain plus the secondary feedback-loop workflow, live, against the fixed demo app, exactly as scoped in the Demo Scope Freeze.  
* **Dependencies:** every module Epic, Sprints 1–10; IH.1.  
* **Outputs:** a rehearsed, repeatable demo run.  
* **Consumes:** the entire assembled system.  
* **Produces:** a demo recording/runbook for repeatability.  
* **Shared packages used:** all.  
* **Modules affected:** all ten modules plus Module 9.  
* **Completion criteria:** one continuous run demonstrates every item in the Freeze's "What Version 1 contains" list with no manual patching between steps.

#### **IH.3 — Security & Red-Team Pass Finalization**

* **Owner:** Security / Platform pod  
* **Purpose:** Run the indirect-prompt-injection red-team suite (F12) against the fully assembled chain, not just Foundation-stage scaffolding.  
* **Dependencies:** F12, IH.2.  
* **Outputs:** a finalized red-team pass report.  
* **Consumes:** F12's portable scenario set; the assembled chain.  
* **Produces:** pass/fail security findings.  
* **Shared packages used:** eval/red-team harness.  
* **Modules affected:** Modules 1, 4, 6, 10 (the named ingestion→action path).  
* **Completion criteria:** every scenario in F12's set runs against real (not stub) module logic with no unresolved high-severity finding.

#### **IH.4 — Cost-Ceiling & Fail-Closed Load Test**

* **Owner:** Platform pod  
* **Purpose:** Verify the per-tenant LLM cost ceiling's fail-closed behavior under a real, multi-module chain, not just F5's unit tests.  
* **Dependencies:** F5, IH.2.  
* **Outputs:** a load-test report.  
* **Consumes:** `llm-gateway-client`'s real cost-ledger under load.  
* **Produces:** verified fail-closed behavior at scale.  
* **Shared packages used:** `llm-gateway-client`.  
* **Modules affected:** every LLM-driven module (1, 2, 3, 5, 6, 8).  
* **Completion criteria:** a deliberately-exhausted tenant ceiling mid-chain fails closed with a human-visible error, never a silent model downgrade or dropped request.

#### **IH.5 — Runbook & On-Call Final Validation**

* **Owner:** Platform pod  
* **Purpose:** Exercise F13's debugging runbook against a simulated incident spanning Langfuse, the Neo4j browser, connector logs, and application logs — with real, not fictional, instrumentation now in place.  
* **Dependencies:** F13, IH.2.  
* **Outputs:** a validated, updated runbook.  
* **Consumes:** every service's observability output.  
* **Produces:** no runtime data — a validated process artifact.  
* **Shared packages used:** none directly.  
* **Modules affected:** cross-cutting.  
* **Completion criteria:** the on-call rotation successfully traces a simulated incident to root cause using only the runbook and live instrumentation.

#### **IH.6 — Staged-Adoption Tracker Stand-Up Confirmation**

* **Owner:** Platform pod  
* **Purpose:** Confirm the standing tracker for the six staged-adoption triggers (Graphiti, Temporal, reranker, self-hosted Langfuse, live SSO/SCIM, legacy adapters) is live and will be reviewed at every future sprint retrospective — process scaffolding inherited as already-decided, not invented fresh in Phase 3.  
* **Dependencies:** none beyond the six triggers already being named in the Freeze.  
* **Outputs:** a live tracker (one ticket per staged item, referencing its Freeze-document trigger verbatim).  
* **Consumes:** the Freeze's Demo Scope Freeze trigger table.  
* **Produces:** no runtime data — a process artifact.  
* **Shared packages used:** none.  
* **Modules affected:** none directly — cross-cutting operational hygiene.  
* **Completion criteria:** all six items are tracked; a standing watch item on Promptfoo's post-acquisition posture is also open, with DeepEval's red-teaming surface named as the fallback.

---

# **Part 4 — Dependency Graph**

## **4.1 Two graphs, not one**

The **sprint sequence** (Part 2) is a build-order and staffing convention: Foundation, then Module 10, then Module 7 substrate, and so on, fixed once per §1.1 for calendar and ownership purposes. The **epic dependency graph** below is the actual data — which specific Epic's Dependencies field names which other specific Epic's output as required before it starts. The two agree most of the time; that agreement is what makes the sprint sequence a sound plan. They diverge in a handful of places, and those divergences matter: they're exactly where a team with enough parallel capacity can save real calendar time without touching the frozen build order, and exactly where assuming "later sprint number always means later start" would introduce a wait nothing in Part 3 actually requires.

Every edge below is copied from a Dependencies field already stated in Part 3. No new dependency is introduced here.

## **4.2 The true critical path**

Tracing only the edges that actually gate a downstream Epic's start (not the full sprint, just the specific Epic that's actually load-bearing) produces a thinner chain than "Sprint 0 → 1 → 2 → … → 11" suggests:

**F1/F3 → F4 → M10.1 → M1.2 ⇢ (converges with M7S.1 → M7S.2) → M1.0b/M1.1 → M2.1 (via M1.0a only) → M3.1 → M4.1 → M6.1 (via M5.2, not the full Module 4/5 build) → IH.2 → IH.3/IH.4/IH.5 → Demo Complete.**

Two convergence points dominate this chain and deserve names:

* **The Sprint-3 convergence.** Module 1 is the first Epic set that genuinely needs *two* independent upstream tracks finished — Module 10's Jira adapter (M10.1, Sprint 1) and Module 7 substrate's real `kg-client` (M7S.2, Sprint 2) — plus its own decision Epic (M1.0a) and boundary contract (M1.0b). This is the first point in the whole plan where parallel work has to rejoin into one thread, and it is why Sprint 3 is scheduled after both Sprint 1 and Sprint 2 rather than after either alone.  
* **The Sprint-11 convergence.** IH.2 is the single Epic with the largest fan-in in the entire plan — "every module Epic, Sprints 1–10" — by design: it is the end-to-end rehearsal, and rehearsing "end to end" only means something once every upstream Epic exists. IH.3, IH.4, and IH.5 each fan back in turn to a specific Sprint-0 Epic (F12, F5, F13 respectively) *and* to IH.2, which is why they cannot be pulled earlier than Sprint 11 even though their Sprint-0 prerequisite has been sitting finished since Sprint 0.

**What is not on the critical path, and why that matters:** M1.1, M1.2, and M1.3 (Module 1's actual extraction logic, ingestion wiring, and eval dataset) are *not* Sprint 4's gating dependency — only M1.0a (the Agent SDK scoping decision, a same-sprint decision Epic) is. Concretely, M2.1 could begin the moment M1.0a is recorded, without waiting for the rest of Module 1 to finish, because M2.1's own Dependencies field names only M1.0a and M7S.5 — never M1.1–M1.3. The sprint-sequence convention still schedules Module 2's *sprint* after Module 1's for staffing and narrative reasons (one module fully demoed before the next begins), but a team that has spare Module 2 capacity mid-Sprint-3 is not blocked by anything in this graph from starting M2.1 early. The same pattern recurs at Sprint 6→7 (Module 5's M5.0–M5.4 depend only on M7S.2/M7S.4, Sprint 2 — never on Module 4) and at Sprint 8 (M6.1 depends on M2.1, M3.3, M5.2 — never directly on Module 4's Sprint-6 Epics). Part 4.4 below names every such case.

## **4.3 Per-sprint dependency tables**

Each table lists only the Epics whose Dependencies field names an Epic from a *different* sprint (a "sprint-crossing" edge). Same-sprint dependencies (e.g., M1.1 depending on M1.0a/M1.0b) are already fully stated in Part 3 and are not repeated here; Part 4 exists to make the *cross-sprint* wiring — the part a single Epic's own entry can't show by itself — visible in one place.

**Sprint 0 — Foundation** (internal cross-epic edges only; nothing here crosses a sprint boundary since Sprint 0 is the root)

| Epic | Depends on (same sprint) |
| ----- | ----- |
| F4 | F3 |
| F5 | F3 |
| F9 | F3 |
| F12 | F1 |
| F13 | F1–F12 (soft; documents their output) |
| F14 | F4 |

F1, F2, F3, F6, F7, F8, F10, F11 have no dependency at all — the eight Day-1 starters (§4.6).

**Sprint 1 — Module 10**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M10.1–M10.4 | F1 (all); F4 (M10.1–M10.3 only) | 0 |
| M10.5 | F1 | 0 |
| M10.6 | F8; M10.1–M10.3 (same sprint) | 0 |

Sprint 1 depends on Sprint 0 only — nothing here reaches back further, and nothing here reaches forward.

**Sprint 2 — Module 7 (Substrate) \+ SI.1**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M7S.1 | F8 | 0 |
| M7S.2 | F2, M7S.1 | 0, same |
| M7S.3 | F8, M7S.1 | 0, same |
| M7S.4 | M7S.2 | same |
| M7S.5 | F8, M7S.1 | 0, same |
| SI.1 | M7S.1 | same |

Sprint 2 depends on Sprint 0 only — **not on Sprint 1.** This is the first parallel-capable pair (§4.4).

**Sprint 3 — Module 1**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M1.0a | F5, F7 | 0 |
| M1.0b | F8, M7S.1 | 0, 2 |
| M1.1 | M1.0a, M1.0b, F7 | same, same, 0 |
| M1.2 | M10.1, M7S.2 | 1, 2 |
| M1.3 | M1.1, F7 | same, 0 |

Sprint 3 is the Sprint-3 convergence named in §4.2 — the first Epic set needing both Sprint 1 and Sprint 2 complete.

**Sprint 4 — Module 2**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M2.1 | M1.0a, M7S.5 | 3, 2 |
| M2.2 | F9 | 0 |
| M2.3 | M7S.2 | 2 |
| M2.4 | M2.1, F7, F9 | same, 0, 0 |

Only M2.1 reaches into Sprint 3, and only as far as M1.0a — not M1.1, M1.2, or M1.3.

**Sprint 5 — Module 3**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M3.1 | M1.0b, M2.1, M7S.5 | 3, 4, 2 |
| M3.2 | M3.1 | same |
| M3.3 | M3.1, M3.2 | same |
| M3.4 | M3.2, F7 | same, 0 |

**Sprint 6 — Module 4**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M4.1 | M3.3, M10.4 | 5, 1 |
| M4.2 | M4.1, F11 | same, 0 |
| M4.3 | M4.2, F6 | same, 0 |
| M4.4 | F6 | 0 |

M10.4 (Sprint 1) has been sitting finished since Sprint 1 — its appearance here is not a new wait, just the point where it's finally consumed.

**Sprint 7 — Module 5**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M5.0 | M7S.2 | 2 |
| M5.1 | M5.0, M1.0a, M7S.5 | same, 3, 2 |
| M5.2 | M7S.1, M5.1 | 2, same |
| M5.3 | F9 | 0 |
| M5.4 | M5.0, M5.1, M7S.4 | same, same, 2 |
| M5.5 | M5.1, F7 | same, 0 |

**Sprint 7 depends on Sprint 2 and Sprint 3 (M1.0a only) — not on Sprint 6.** The second parallel-capable pair (§4.4): Module 5's classification logic is built and eval-tested against M5.0's fixture, per the same stub-and-swap discipline used at the Foundation boundary (§1.2), and never waits on Module 4's real execution results to exist.

**Sprint 8 — Module 6**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M6.1 | M2.1, M3.3, M5.2 | 4, 5, 7 |
| M6.2 | M6.1, M5.2 | same, 7 |
| M6.3 | SI.1, M10.2, M6.1 | 2, 1, same |
| M6.4 | M6.1, F7 | same, 0 |

Sprint 8 reaches into Sprints 4, 5, 7, 2, and 1 — but **not Sprint 6.** Module 6 aggregates Risk Assessment (Module 2), Test Case approval (Module 3), and Defect Report/waiver (Module 5) directly; it reads Module 4's Observation/Execution Result entities only indirectly, through the graph, the same graph-mediated pattern noted in §4.4.

**Sprint 9 — Module 7 (Product Surface)**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M7P.1 | M7S.2, M7S.4 | 2, 2 |
| M7P.2 | M7P.1, SI.1 | same, 2 |
| M7P.3 | M7P.1 | same |
| M7P.4 | M7P.1, F7 | same, 0 |

Sprint 9's Epics depend technically on **Sprint 2 alone.** Its Sprint-9 calendar position is a deliberate demo-quality decision (ADR-012; §Sprint 9 Purpose, Part 2) — the graph needs to hold real, multi-module data before the query surface is demo-worthy — not a technical blocking dependency. This is the clearest case in the whole plan of a sprint position set by narrative judgment rather than a hard edge, and it is named as such rather than left to look like a dependency it isn't.

**Sprint 10 — Module 8**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| M8.0 | none but Sprint 9's build-order position | — |
| M8.1 | M8.0, M7S.1 | same, 2 |
| M8.2 | M8.1, M1.1, M7S.2 | same, **3**, 2 |
| M8.3 | M8.2, F7 | same, 0 |

M8.2's reach back to M1.1 (Sprint 3) — reusing Module 1's extraction pattern — is the single longest non-adjacent cross-sprint edge outside of Sprint 11's integration Epics.

**Module 9 continuous track** — each row's "Depends on" column in the Part 3 table is already same-sprint by construction (per §1.1's design), so no separate cross-sprint table is needed here; see Part 3 directly.

**Sprint 11 — Integration Hardening**

| Epic | Depends on | From sprint |
| ----- | ----- | ----- |
| IH.1 | M9.T0–M9.T10 | 0–10 (all) |
| IH.2 | every module Epic, Sprints 1–10; IH.1 | 1–10 (all), same |
| IH.3 | F12, IH.2 | 0, same |
| IH.4 | F5, IH.2 | 0, same |
| IH.5 | F13, IH.2 | 0, same |
| IH.6 | none beyond the Freeze's own trigger table | — |

IH.2 has the largest fan-in of any Epic in the plan by design (§4.2). IH.3–IH.5 each reach all the way back to a specific Sprint-0 Epic that has been sitting finished for eleven sprints — the wait here is entirely for IH.2's rehearsal, not for F5/F12/F13 themselves.

## **4.4 Parallel-capable sprint pairs**

Three pairs of adjacent-numbered sprints have **no direct epic-to-epic dependency** on each other, meaning a team with two independently-staffed pods could run them concurrently without violating any dependency this document states, even though the sprint sequence numbers them sequentially for ownership and narrative purposes (§1.1):

| Pair | Why they're independent | What still keeps them sequential in the roadmap |
| ----- | ----- | ----- |
| **Sprint 1 (Module 10) ∥ Sprint 2 (Module 7 substrate)** | Neither M10.1–M10.6 nor M7S.1–M7S.5/SI.1 names an Epic from the other sprint as a Dependency. Both depend only on Sprint 0. | Sprint 3 (Module 1) needs both finished; running them in parallel, not series, is the way to reach Sprint 3 fastest — the roadmap's numbering reflects a staffing default (one pod at a time), not a technical wait. |
| **Sprint 6 (Module 4) ∥ Sprint 7 (Module 5)** | Module 5's Epics depend on Sprint 2 (M7S.2/M7S.4) and Sprint 3 (M1.0a) only — never on Module 4. This is M5.0's fixture-backed decoupling (§1.2, Modularity Audit Exception 1) doing its job. | Module 6 (Sprint 8) needs Module 5's output (M5.2) but not Module 4's directly (per its own Dependencies field); running 6 and 7 in parallel shortens the path to Sprint 8, not just to Sprint 7. |
| **Sprint 9 (Module 7 surface) ∥ Sprints 3–8** | M7P.1–M7P.4 depend on Sprint 2 alone. | Held to Sprint 9 by deliberate demo-narrative sequencing (ADR-012), not a technical gate — see §4.3's note on Sprint 9. A team could build the surface earlier; the plan chooses not to, on purpose, so the demo doesn't show a thin graph. |

**What this does not change:** the sprint numbering in Part 2 remains the roadmap of record for staffing, ownership, and the Definition-of-Done sequence. §4.4 is a reading of the same frozen Epics' own stated dependencies, offered because a Platform lead planning pod capacity needs to know where slack genuinely exists — it is not a proposal to renumber anything.

## **4.5 Graph-mediated soft dependencies**

Several Epics consume another module's data exclusively through `kg-client` and the Knowledge Graph rather than through a direct Epic-to-Epic handoff — Principle #6's "no module reaches into another module's internals" enforced structurally (§1.3). This means the *explicit* Dependencies fields in Part 3 understate real data flow in one specific, consistent way: an Epic that reads Module 4's Observation/Execution Result entities (e.g., Module 5's real-data operation, Module 6's aggregation) does not name M4.2 as a Dependency, because what it actually depends on is "the graph contains this entity type," which `kg-client` and the schema (M7S.1) already guarantee structurally regardless of which sprint happens to have populated a given instance. This is a feature of the architecture, not a gap in this document: it is exactly why Module 5 can build against M5.0's fixture and Module 6 can build its aggregation logic without a hard wait on Module 4's calendar slot. Nothing in §4.3–§4.4 above should be read as claiming these modules never use each other's data — only that the *build-time* dependency is on the schema and `kg-client` (both Sprint 2), not on the specific sprint that first happens to populate an instance.

## **4.6 Fully independent Epics (zero dependency)**

Epics with no Dependencies field pointing to any other Epic — the true Day-1 (or, for IH.6, "any day") starters:

* **Sprint 0:** F1, F2, F3, F6, F7, F8, F10, F11 — eight of Foundation's fourteen Epics, confirming §1.5's "nearly all run fully in parallel" claim at the Epic level, not just as an assertion.  
* **Sprint 10:** M8.0 — its only stated dependency is "Sprint 9's completion (build-order position)," a calendar/staffing dependency, not a technical one; the validation spike itself could run the moment a Platform lead and the Module 8 team are free.  
* **Sprint 11:** IH.6 — depends on nothing but the Freeze's own Demo Scope Freeze trigger table, which has existed since before Sprint 0. It is scheduled in Sprint 11 for a final confirmation pass, not because anything blocks it from being a standing, continuously-live tracker from day one (and Part 3's own text for IH.6 says exactly this).

## **4.7 Shared-infrastructure convergence points**

Two artifacts sit at the center of the graph — the points where the largest number of independent Epics' arrows all terminate:

* **`packages/schemas`.** M7S.1 (Sprint 2) is a direct or indirect Dependency of M7S.2, M7S.3, M7S.5, SI.1, M1.0b, M8.1 — and, through those, nearly everything built afterward. This is why §1.3 makes it the one package that is Human-Owned and gated by the compatibility-check harness on every change: a slip or an unreviewed break here doesn't cost one Epic, it costs every Epic downstream of Sprint 2.  
* **`kg-client`.** M7S.2 (Sprint 2) is a named Dependency of M1.2, M2.3, M5.0, M5.4, M7P.1, M8.1, M8.2 directly, and an implicit graph-mediated dependency (§4.5) of every other module's read/write path. Its Sprint-2 completion is the single event that unblocks the largest number of downstream Epics of anything in the plan except `packages/schemas` itself.

Part 5 below states, for every shared package and service, exactly which Epic creates it, who owns it afterward, and when it becomes read-only to everyone but its owner.

---

# **Part 5 — Shared Infrastructure Allocation**

Every shared package or service in the Freeze's own Shared Infrastructure table (and the two this document's Part 3 adds — `ui-components` and `rendering`'s scaffold owner) has exactly one creating Epic, one owner, a stated freeze point, a stated read-only point, and a stated extension mechanism. No shared artifact is created twice, and no artifact is owned by "the team that happens to need it next."

## **5.1 Master allocation table**

| Component | Created by | Owner (post-creation) | Primary consumers | Freeze point | Read-only point | Extension mechanism |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| `packages/connector-contract` | F1 (Sprint 0) | Foundation pod / Connector sub-lead | Module 10 directly; Modules 1, 4, 6 indirectly | Contract interface frozen at F1's completion criteria | After M10.1–M10.5 all pass the generic contract-test suite (end of Sprint 1) | New tool \= new adapter implementing the existing contract; the contract itself changes only through a human-reviewed change, never a per-adapter workaround |
| `packages/kg-client` | F2 stub (Sprint 0) → M7S.2 real (Sprint 2) | Module 7 team | Every graph-touching module (1, 2, 5, 6, 7, 8) | Public method signatures frozen at F2 so the Sprint-2 swap requires zero consumer changes; tenant-scoping enforcement frozen at M7S.2 | Immediately at M7S.2 — no code path outside `kg-client` may issue a Cypher query, enforced by lint/CI, not convention (ADR-011) | New query methods added by the Module 7 team on request from a consuming module; the tenant-scoping chokepoint itself is never reopened |
| `packages/schemas` | F8 scaffold (Sprint 0) → M7S.1 ten-entity authoring (Sprint 2) | Module 7 team (schema authority, per M7S.5) | All ten modules, all services | Each entity type is additive-only from the moment it merges (M7S.1) | Human-Owned from first entity onward (Code Ownership Matrix) — no AI coding session is ever the last reviewer on a change here | Additive-only: new attributes/entities via PR, gated by the compatibility-check harness (M7S.3); a rename or removal requires a deprecation window, never a silent break |
| `packages/llm-gateway-client` | F5 (Sprint 0) | Foundation pod / Gateway sub-lead → Platform pod | Every LLM-driven module (1, 2, 3, 5, 6, 8) | Fail-closed cost-ceiling behavior and the sole-path enforcement (Rule A5) frozen at F5 | Wrapper/enforcement code Human-Owned and read-only to AI sessions from Sprint 0 | New model routes added as config entries in `infra/litellm/`, never as new code paths that bypass the gateway |
| `packages/config-service` | F9 (Sprint 0) | Foundation pod / Config sub-lead | Modules 2 and 5 (calibrated values); the gateway's routing table | Versioning/tenant-override mechanism frozen at F9 | Mechanism read-only after F9; the *values* it holds stay provisional until each module's own calibration process (M2.2, M5.3) says otherwise | New calibrated values registered through the existing versioning API — no core-package change needed per new value |
| `packages/rendering` | SI.1 (Sprint 2) | Shared Infrastructure pod (distinct from Module 7) | Module 6 (M6.3), Module 9 (continuous), Module 7 surface (M7P.2) | Core "structured, cited entities → human artifact" transformation contract frozen at SI.1 | Interface read-only after SI.1; templates are additive | New per-consumer templates (go/no-go brief, cited answer, dashboard cards) added by the consuming module team, conforming to SI.1's interface — never a new transformation mechanism |
| `packages/ui-components` | F14 (Sprint 0) | Module 9 team | `apps/web`; any future admin surface | shadcn/ui \+ Tailwind baseline pinned at F14 | Never — this is the one shared package with a single owning consumer throughout | Module 9 extends its own component set continuously across M9.T1–M9.T10 |
| `packages/extraction` | *(see note below)* | Foundation pod → Platform pod | Modules 1, 6, 8 (per the Freeze's Shared Infrastructure table) | Instructor/Pydantic-AI backbone pattern, bundled with F8's Pydantic layer | Human-Owned initial setup; routine usage is an AI-generation candidate once the pattern exists (mirrors the Code Ownership Matrix's own treatment of the schema codegen toolchain) | New structured-output call sites import the existing backbone; no module writes its own parse-and-retry loop (Principle #3) |
| Eval harness (DeepEval/RAGAS/Promptfoo) \+ mutation-testing | F7 CI wiring (Sprint 0) → M3.2 Stryker wiring (Sprint 5) | Foundation pod / Eval sub-lead (harness); each module team (its own dataset) | Every LLM-driven module (1, 2, 3, 5, 6, 8) | CI gate mechanism frozen at F7; mutation-testing mechanism frozen at M3.2 | Harness wiring Human-Owned and read-only; individual eval datasets are each module's own additive content (Code Ownership Matrix: harness vs. test cases split) | New datasets added under `evals/module-XX/`, no harness-code change required; a new mutation-testing engine (mutmut, cosmic-ray, PIT) documented but only wired in when a module in that language exists |
| Observability (OpenTelemetry, `structlog`, Langfuse) | F10 (Sprint 0) | Foundation pod / Observability sub-lead → Platform pod | Every service | Instrumentation standard frozen at F10; hosting model staged (managed → self-hosted at trigger, per Demo Scope Freeze) | Instrumentation pattern fixed at F10; each service's own trace/log content is that service team's, not a shared-package edit | Self-hosted Langfuse migration is a config/deployment change at its named trigger, not a re-instrumentation |
| Object storage \+ backup/DR | F11 (Sprint 0) | Foundation pod / Storage sub-lead → Platform pod | Module 4 (trace archives) primarily | Retention window \+ backup/DR policy frozen at F11 | Policy Human-Owned; trace-artifact writes are Module 4's own runtime data | Retention tiering is a named Phase 2+ trigger (Demo Scope Freeze), not a Sprint-Architecture-scope change |
| Security threat model \+ red-team suite | F12 (Sprint 0) | Foundation pod / Security sub-lead → Security/Platform pod | Modules 1, 4, 6, 10 (the named ingestion→action path) | Threat model document \+ portable scenario set frozen at F12 | Human-Owned throughout (Code Ownership Matrix) | Finalized against the fully assembled chain at IH.3 (Sprint 11); new scenarios added as portable test data, never Promptfoo-specific logic (Rule A8) |
| Authentication (WorkOS) | F4 (Sprint 0) | Foundation pod / Auth sub-lead | `services/api`; transitively every module | Stub-check interface frozen at F4 so consumer code doesn't change when live SSO/SCIM lands | Human-Owned, buy-not-build, decide-once | Live per-partner SSO/SCIM configuration is an onboarding-time config action, never a code change |
| Operational readiness (on-call, runbook, lockfiles) | F13 (Sprint 0) | Foundation pod / Platform lead | Cross-cutting (all seven foundation-layer services) | v0 runbook and on-call assignment frozen at Sprint 0 exit | Not applicable — this is process/policy, not code | Runbook validated against real instrumentation and finalized at IH.5 (Sprint 11) |
| Orchestrator (LangGraph skeleton; Temporal scaffold) | F6 (Sprint 0) | Foundation pod / Orchestration sub-lead | Modules 1–6, 8 | Skeleton frozen at F6; self-verification gate frozen at M4.3 (Sprint 6); Temporal remains inactive behind its feature flag | Human-Owned (Code Ownership Matrix: "core abstraction... not a place to let an AI-generated first draft silently miss a gate") | Temporal activation is a named staged-adoption trigger (Demo Scope Freeze), not a Sprint-Architecture-scope change |
| Schema codegen toolchain (Pydantic → `quicktype` → TypeScript) | F8 (Sprint 0) | Foundation pod / Schema sub-lead | Every `packages/schemas` consumer (API, web, all modules) | Pipeline mechanism frozen at F8 | Human-Owned initial setup; routine regeneration after a schema change is AI-generation-safe once the pipeline exists (Code Ownership Matrix) | Regeneration is CI-atomic with every schema PR (Rule A2/A6 territory) — never a manual, skippable step |
| Connector-model codegen (`datamodel-code-generator`, OpenAPI → Pydantic) | M10.6 (Sprint 1) | Module 10 team | Module 10's own adapters only | Frozen at M10.6; scoped exclusively to connector request/response models, never `packages/schemas` | Not shared beyond Module 10 — no read-only concern | Regenerating from a spec change is a clean, isolated diff inside Module 10's own subfolder |
| `services/graph-service` | F2 infra (Sprint 0) → M7S.2–M7S.4 substrate logic (Sprint 2) → M7P.1–M7P.2 surface logic (Sprint 9) | Module 7 team, throughout | Modules 1, 2, 5, 6, 8 (substrate); Module 9 (surface) | Substrate logic frozen at Sprint 2's exit gate; surface logic frozen at Sprint 9's exit gate | Tenant-scoping enforcement layer read-only from M7S.2 onward (same as `kg-client`, above) | Text-to-Cypher query patterns extended by the Module 7 team as new question types are demo-scripted |
| `mutation-testing/` (top-level folder, not a `packages/` import) | M3.2 (Sprint 5) | Module 3 team | Module 3 only at V1 | Stryker config frozen at M3.2; mutmut/cosmic-ray/PIT configs documented, not CI-wired, until a codebase in that language exists | Not a shared package — no cross-team read-only concern | A second engine is wired into CI only when a module in that language is actually built (Phase 2+, per the Freeze's own repo-structure note) |

## **5.2 The two-stage freeze pattern**

Three components — `kg-client`, `packages/schemas`, and (in spirit) the Module 5 ↔ Module 7 boundary via M5.0 — freeze twice, not once: an interface/stub freeze early (Sprint 0 or the fixture in M5.0), then a real-implementation freeze later (Sprint 2, or the M5.4 swap-in), with the guarantee — stated once, here — that **no consumer-facing signature changes between the two freezes.** This is the stub-and-swap mechanism (§1.2) restated as a shared-infrastructure allocation rule: an Epic that builds against the stub is never rebuilding anything when the real backend lands, because the interface was the thing frozen first, deliberately, precisely so the swap would be silent.

## **5.3 A gap this document did not silently fix**

`packages/extraction` (the Instructor/Pydantic-AI structured-extraction backbone) is named in the Freeze's own Shared Infrastructure table as a first-class shared component consumed by Modules 1, 6, and 8 — but neither this document's Sprint 0 Epic list (F1–F14) nor the Implementation Audit's Code Ownership Matrix names an explicit creating Epic or an explicit ownership row for it. The allocation above (bundled into F8, ownership inferred by analogy to the schema codegen toolchain's own Human-Owned-setup/AI-generation-safe-usage split) is this document's best-supported inference, not a fact restated from Part 3 the way every other row above is. It is flagged here, and in Appendix A at the end of this document, rather than corrected by quietly inserting a new "F15" into the already-frozen Sprint 0 Epic list.

---

# **Part 6 — Prompt Ownership Matrix**

This is a numbering reservation, not a prompt list. No prompt is written here; Phase 3 (Atomic Task Planning) writes them. What's fixed here is which number range belongs to which Epic, so that when Phase 3 decomposes an Epic into Features, Components, and Atomic Implementation Units, every resulting prompt has an unambiguous, collision-free number before a single one is drafted — and so two Phase-3 sessions working different Epics can never accidentally claim the same number.

## **6.1 Allocation convention**

Each Epic receives a starting block of ten prompt numbers. Ten is a provisional reservation, not a cap: it is enough for most Epics' eventual Feature/Component/Atomic-Unit breakdown without wasting the number space, and it is deliberately small enough that Sprint 0's fourteen genuinely-small Epics don't inflate the whole scheme the way giving every Epic a 30-number block (this document's own opening instruction's example size) would. Sprint boundaries fall on round numbers so a range is always human-scannable by sprint alone.

**Overflow rule, stated once:** if an Epic's Phase 3 decomposition needs more than ten numbers, the next unclaimed number *inside that Epic's own sprint range* is used first (every sprint range below carries small unallocated gaps for exactly this reason). If a sprint's entire range is exhausted, a new sub-range is appended immediately after Sprint 11's block (0771 onward) and cross-referenced back to the exhausted sprint — an Epic's prompts are never renumbered to make room, only extended.

## **6.2 Master range table**

| Sprint | Scope | Epics | Prompt range | Folder scope |
| ----- | ----- | ----- | ----- | ----- |
| 0 | Foundation | F1–F14 | 0001–0140 | `packages/connector-contract`, `packages/kg-client` (stub), `infra/postgres`, `services/api` (auth stub), `packages/llm-gateway-client`, `services/orchestrator` (skeleton), eval CI wiring, `packages/schemas` (scaffold), `packages/config-service`, observability wiring, `infra/` (storage, security docs, on-call), `apps/web` (shell) |
| 1 | Module 10 \+ Module 9 (M9.T1) | M10.1–M10.6, M9.T1 | 0141–0210 | `services/connectors/*` |
| 2 | Module 7 substrate \+ SI.1 \+ Module 9 (M9.T2) | M7S.1–M7S.5, SI.1, M9.T2 | 0211–0280 | `services/graph-service` (substrate), `packages/schemas` (ten-entity \+ trust indicator), `packages/rendering` (scaffold) |
| 3 | Module 1 \+ Module 9 (M9.T3) | M1.0a, M1.0b, M1.1–M1.3, M9.T3 | 0281–0340 | `modules/module-01-requirement-intelligence/` |
| 4 | Module 2 \+ Module 9 (M9.T4) | M2.1–M2.4, M9.T4 | 0341–0390 | `modules/module-02-risk-strategy/` |
| 5 | Module 3 \+ Module 9 (M9.T5) | M3.1–M3.4, M9.T5 | 0391–0440 | `modules/module-03-test-generation/`, `mutation-testing/` |
| 6 | Module 4 \+ Module 9 (M9.T6) | M4.1–M4.4, M9.T6 | 0441–0490 | `modules/module-04-execution-orchestration/`, `infra/temporal/` |
| 7 | Module 5 \+ Module 9 (M9.T7) | M5.0–M5.5, M9.T7 | 0491–0560 | `modules/module-05-defect-triage/` |
| 8 | Module 6 \+ Module 9 (M9.T8) | M6.1–M6.4, M9.T8 | 0561–0610 | `modules/module-06-release-readiness/` |
| 9 | Module 7 surface \+ Module 9 (M9.T9) | M7P.1–M7P.4, M9.T9 | 0611–0660 | `services/graph-service` (surface) |
| 10 | Module 8 \+ Module 9 (M9.T10) | M8.0–M8.3, M9.T10 | 0661–0710 | `modules/module-08-feedback-learning-loop/` |
| 11 | Integration Hardening | IH.1–IH.6 | 0711–0770 | `apps/web` (final), cross-cutting (security, cost, runbook, tracker) |

`M9.T0` is not a separate line above — it is F14 (Sprint 0, prompts 0131–0140), per Part 3's own note that Part 3 already places it there.

## **6.3 The Module 9 corridor, viewed as one sequence**

The table above scopes each Module 9 continuous-track Epic to the sprint it's scheduled inside, matching Part 3's own treatment. For the Module 9 team specifically — the one team with work in every sprint — the same eleven Epics read as a single ascending sequence for their own planning convenience, without changing a single number assigned above:

`0131–0140 (M9.T0/F14) → 0201–0210 (M9.T1) → 0271–0280 (M9.T2) → 0331–0340 (M9.T3) → 0381–0390 (M9.T4) → 0431–0440 (M9.T5) → 0481–0490 (M9.T6) → 0551–0560 (M9.T7) → 0601–0610 (M9.T8) → 0651–0660 (M9.T9) → 0701–0710 (M9.T10) → 0711–0770 (IH.1, folded into Sprint 11's own range since it is Module 9's final-hardening Epic, not a distinct continuous-track row)`

## **6.4 Shared-infrastructure corridor cross-reference**

Prompts touching a Human-Owned shared package (§5.1, Code Ownership Matrix) are never confined to one sprint's range — `packages/schemas`, for instance, is written at 0211–0280 (Sprint 2) but every later sprint's Epics that add an additive schema attribute (none currently named beyond Sprint 2, per Part 3) would file under the *consuming* Epic's own range, with a mandatory cross-reference back to 0211–0280 in the prompt's own header. This is a documentation convention Phase 3 inherits, not a new numbering rule: shared-package prompts live in their origin Epic's range; every *consumer's* prompt that touches that same package cites the origin range rather than claiming a new one.

---

# **Part 7 — Merge Conflict Prevention**

Every mechanism below already exists somewhere in Parts 1–6; Part 7 collects them into one operational answer to a single question — **"how do we know two AI coding sessions, working the same sprint, will never write to the same file?"**

## **7.1 Folder ownership, by sprint**

One Epic owns one folder (or one clearly bounded subfolder) per sprint; no two Epics in the same sprint own the same folder; no Epic ever writes outside its own folder plus its declared shared-package imports.

| Sprint | Folder(s) in play | Owning Epic(s) |
| ----- | ----- | ----- |
| 0 | `packages/connector-contract/` | F1 |
| 0 | `packages/kg-client/` (stub), `infra/neo4j/` | F2 |
| 0 | `infra/postgres/` | F3 |
| 0 | `services/api/` (auth stub) | F4 |
| 0 | `packages/llm-gateway-client/`, `infra/litellm/` | F5 |
| 0 | `services/orchestrator/` (skeleton), `infra/temporal/` (manifest only) | F6 |
| 0 | `prompts/`, `evals/` (empty scaffolds), Langfuse Prompt Management wiring | F7 |
| 0 | `packages/schemas/` (scaffold) | F8 |
| 0 | `packages/config-service/` | F9 |
| 0 | Observability wiring (cross-cutting instrumentation calls inside every other Epic's own files, not a folder of its own) | F10 |
| 0 | `infra/deploy/` (object storage \+ DR policy) | F11 |
| 0 | `docs/` (threat model), red-team scenario data | F12 |
| 0 | Documentation/process only — no source folder | F13 |
| 0 | `apps/web/` (shell), `packages/ui-components/` | F14 / M9.T0 |
| 1 | `services/connectors/jira/` | M10.1 |
| 1 | `services/connectors/github/` | M10.2 |
| 1 | `services/connectors/slack/` | M10.3 |
| 1 | `services/connectors/playwright/` | M10.4 |
| 1 | `services/connectors/legacy/` (test-fake only) | M10.5 |
| 1 | Adapter-local generated models, inside each of the above | M10.6 |
| 2 | `packages/schemas/` (ten-entity types) | M7S.1 |
| 2 | `packages/kg-client/` (real) | M7S.2 |
| 2 | Compatibility-check harness (lives alongside `packages/schemas/`, CI-invoked) | M7S.3 |
| 2 | `services/graph-service/` (construction wiring) | M7S.4 |
| 2 | `packages/schemas/` (trust-indicator type — same folder as M7S.1, sequenced after it) | M7S.5 |
| 2 | `packages/rendering/` (v0 scaffold) | SI.1 |
| 3 | Decision record only — no source folder | M1.0a |
| 3 | `packages/schemas/` (boundary contract — same folder as M7S.1/M7S.5, sequenced after both) | M1.0b |
| 3–10 | `modules/module-0X-*/` | Each sprint's named module Epics, one module folder per sprint |
| 11 | `apps/web/` (final hardening) | IH.1 |
| 11 | Cross-cutting: rehearsal runbook, security docs, load-test report, on-call runbook, tracker (no exclusive source folder) | IH.2–IH.6 |

**The one recurring exception, named once:** `packages/schemas/` is written into by M7S.1 (Sprint 2), M7S.5 (Sprint 2, same sprint), and M1.0b (Sprint 3) — three different Epics, two different sprints, one folder. This is exactly the case §1.3 and §7.3 exist for: every one of those three writes goes through the same gate (Human review \+ compatibility-check harness), sequenced (M7S.1 before M7S.5 before M1.0b, since each needs the prior's types to reference), never concurrent.

## **7.2 AI coding session scoping**

An AI coding session assigned one Epic receives: read/write access to that Epic's own folder (per §7.1); read-only access to every `packages/*` its Consumes field names (Part 3); and nothing else. It cannot open, and is never handed, another module's folder, another sprint's in-progress Epic, or a shared package outside its declared imports. This is Principle #6 enforced as a literal access-scoping rule, not a request to the model to behave — two sessions working two Epics in the same sprint have no folder in common to diverge on, by construction, per §1.3.

## **7.3 Shared-package change policy**

Every shared package inherits its Code-Ownership-Matrix classification (Human-Owned / AI-Generated-candidate / Hybrid), restated from the Implementation Audit and cross-referenced against Part 5's allocation table:

* **Human-Owned** (`kg-client`, `packages/schemas`, `connector-contract`'s interface, `llm-gateway-client`, `config-service`, the eval-harness wiring itself, the schema-migration/compatibility-check harness, the threat model \+ red-team authorship, the LangGraph orchestration skeleton, auth integration): no AI coding session is ever the last reviewer on a change. A consuming module's AI session may *propose* a change (e.g., a new `kg-client` query method) as a diff, but it merges only after the owning team's human review — never on a passing test suite alone.  
* **AI-Generated, human-reviewed** (connector adapters, CRUD/API endpoints, Module 9 dashboard components, unit/integration tests, documentation): an AI session may merge its own Epic's work once Part 8's gates pass and a human reviewer signs off — the review is lighter-weight than a Human-Owned change, but it still exists.  
* **Hybrid** (DSPy signatures — rubric/taxonomy human-authored, compile-step AI-generation-safe; `packages/rendering` — initial scaffold human-drafted, per-consumer templates AI-generation-safe; the schema codegen toolchain — initial setup human, routine regeneration AI-safe): the split is stated once per package in Part 5 and never re-litigated per Epic.

**The rule that actually prevents conflicts:** every shared package has exactly one owning team (Part 5, column 2). A request to change it — whether the requester is an AI session or a human engineer on a different team — is a pull request against the owning team's folder, reviewed by the owning team, never a direct commit by the requesting Epic's own session. This is what makes "two AI agents can't silently diverge on the same file" (§1.3) true in practice and not just in principle: there is always exactly one team with merge rights on any given shared file, regardless of how many teams read it.

## **7.4 Schema-specific merge discipline**

Restated once, precisely, because it is the highest-blast-radius file in the repository (§4.7): every PR touching `packages/schemas` must (a) be additive-only — no rename or removal without a stated deprecation window (M7S.3's own completion criteria); (b) regenerate matching TypeScript in the same CI run, atomically (F8, Rule A2/A6 territory); (c) pass the compatibility-check harness against every currently-declared consumer's read path (M7S.3); and (d) receive Human-Owned review, never an AI-session-only merge. A schema PR that fails any one of these four is blocked in CI before it reaches a human reviewer at all — the gate is mechanical first, judgment-based second.

## **7.5 Generated-code policy**

Two codegen pipelines exist, and neither's output is ever hand-edited:

* **`packages/schemas` → TypeScript** (Pydantic `.model_json_schema()` → `quicktype`, F8): regenerated automatically in the same CI run as any Python-side schema change (§7.4). A PR that edits the generated TypeScript directly, without a corresponding Python-side change, fails CI on drift.  
* **Connector OpenAPI → Pydantic** (`datamodel-code-generator`, M10.6, scoped to Module 10 only): regenerated from each tool's own published spec; a PR editing a generated connector model directly, rather than regenerating from a spec change, fails the same drift check inside Module 10's own subfolder.

Neither generated tree is a place for an AI coding session to "helpfully" hand-fix a bug — a wrong generated type means the source model or the spec is wrong, and the fix happens there.

## **7.6 Read-only boundary timeline**

Restated from Part 5, collected into one timeline so a Platform lead can answer "is this file safe to touch yet" without cross-referencing every row individually:

| When | What becomes read-only (except to its owning team) |
| ----- | ----- |
| End of Sprint 0 | `packages/connector-contract`'s interface (frozen at F1, though formally exercised through Sprint 1); `packages/llm-gateway-client`'s enforcement code; `packages/config-service`'s versioning mechanism; the LangGraph skeleton's gate-wiring pattern; the eval-harness CI wiring itself |
| Immediately at M7S.2 (Sprint 2) | `kg-client` — the sole permitted Cypher-query path, enforced by lint/CI (ADR-011) |
| From first entity onward (Sprint 2) | `packages/schemas` — Human-Owned from M7S.1's first merge |
| End of Sprint 1 | `connector-contract`'s interface, formally, once all five Sprint-1 adapters (four real \+ one fake) pass the generic contract-test suite |
| After SI.1 (Sprint 2) | `packages/rendering`'s core transformation interface (per-consumer templates remain additive and open) |
| After M3.2 (Sprint 5) | The Stryker mutation-testing configuration (a second engine's config may be added later without touching this one) |

## **7.7 Branching strategy**

Trunk-based, one short-lived branch per Epic, named for the Epic ID (`epic/f5-llm-gateway`, `epic/m3.1-test-case-generation`), never for a person or a sprint. A branch touches only its own Epic's declared folder (§7.1) plus, where a shared-package change is genuinely needed, a *separate* branch scoped to that package alone and reviewed by its owning team (§7.3) — an Epic branch never carries both its own module code and a shared-package edit in the same diff, so a shared-package review is never blocked waiting on unrelated module-specific review comments to resolve. Branches merge to trunk only after Part 8's gates pass for that Epic; trunk itself is always in a state where the next sprint's Epics could branch from it without inheriting a half-finished shared-package change.

## **7.8 Integration sequence within a sprint**

Where a sprint contains both a shared-infrastructure Epic and Epics that consume it in the same sprint (Sprint 2's M7S.1 → M7S.2/M7S.3/M7S.5/SI.1; Sprint 0's F3 → F4/F5/F9), the shared-infrastructure Epic merges to trunk first, and consuming Epics branch from trunk *after* that merge, not from a stale point before it. This is already implied by each Epic's own Dependencies field (Part 3, Part 4) — §7.8 states it here as the literal merge-order rule a release engineer follows, rather than leaving it implicit in the dependency graph alone.

# **Part 8 — Verification Gates**

Every sprint's Definition of Done in Part 2 invokes "every Part 8 gate passes" without, until now, stating what that gate set actually checks. This Part closes that reference, once, so no sprint — and no Epic within it — reopens the question of what "done" mechanically means.

## **8.1 The universal gate**

One set of eight checks applies to every Epic in every sprint, without exception. This is the literal content behind "every Part 8 gate passes":

| Gate | What it mechanically checks | Enforced by |
| ----- | ----- | ----- |
| Build passes | Every workspace touched by the merging diff builds clean against the pinned lockfiles (`uv.lock` for Python, `pnpm-lock.yaml` for Node — both F13) | CI, every PR |
| Tests pass | The Epic's own unit/integration tests; for any LLM-driven Epic, its attached evaluation dataset (Principle #8, F7); for Module 3 specifically, the mutation-testing pass (M3.2) | CI, every PR |
| Imports valid | No `modules/module-0X/` folder imports another module folder's internals (Principle #6); no raw provider SDK import (`anthropic`, `openai`) outside `packages/llm-gateway-client` (Rule A5); no `langgraph.prebuilt` import (Dependency Audit #6) | lint/CI, every PR |
| Interfaces stable | The Epic's build doesn't break against any dependency's interface as frozen at that dependency's Freeze point (Part 5, column 5) — e.g., a Sprint 3+ Epic never breaks against `kg-client`'s public method signatures, frozen at F2 | contract test suite, every PR touching a Part 5 component |
| Schemas synchronized | Any `packages/schemas` change regenerates matching TypeScript in the same CI run (F8); the compatibility-check harness passes against every currently-declared consumer's read path (M7S.3) | CI, every PR touching `packages/schemas` |
| No dependency drift | Every dependency remains pinned to its exact Technology Audit version; a DSPy or LangGraph version bump re-runs the full evaluation suite as a merge gate, identically to a prompt-content change (Rule A3, §1.4) | CI version-pin check \+ eval harness, every PR |
| No deprecated APIs | No code path uses a pattern named stale in the Implementation Audit — see §8.7's living list | lint/CI, every PR |
| No ownership violations | A PR touching a Human-Owned package (Part 5; §7.3) merges only after that package's owning team reviews it — never on a passing test suite alone | branch protection \+ required review, every PR |

These eight checks run identically whether the Epic's code was written by a human engineer or an AI coding session (§7.2) — the gate itself does not know or care which. What differs by author is never *what* is checked; it is *who* signs off, and that split is §7.3's Code-Ownership classification, restated operationally at §8.5.

## **8.2 Gate sequence: mechanical first, judgment-based second**

Generalized from §7.4's own framing to every gate in §8.1, not only schema PRs: the first seven rows above (build, tests, imports, interfaces, schemas, dependency drift, deprecated APIs) are CI checks that block a merge before any human ever opens the diff. Only the eighth row — ownership — is a human step, and it is always the *last* gate a passing PR meets, never the first. A PR that would fail mechanically never consumes an owning team's review time; a PR that passes mechanically still cannot merge on that basis alone if it touches a Human-Owned package.

## **8.3 Sprint-specific additive gates**

Every sprint's Definition of Done in Part 2 names one or two gates beyond the universal eight — items specific enough to that sprint's Epics that folding them into a generic checklist would understate what actually has to be true before the sprint is called complete. Collected here, cross-referenced to their Part 2 origin, so sprint-exit readiness is one table instead of ten re-scanned paragraphs:

| Sprint | Additive gate (beyond §8.1) | Producing Epic(s) |
| ----- | ----- | ----- |
| 0 | Every Technology Audit version is pinned in a committed lockfile; the on-call rotation has a named first pager-holder; `kg-client` and the auth check are explicitly documented as stub-quality, never silently assumed complete | F13, F2, F4 |
| 1 | All four V1 adapters are demo-ready; the legacy adapter is present only as a contract-test fake — zero real Selenium/Appium/BrowserStack code | M10.1–M10.4, M10.5 |
| 2 | The compatibility-check harness's first real exercise passes; a missed-tenant-filter test provably cannot leak a second tenant's data | M7S.3, M7S.2 |
| 3 | The Agent SDK scoping decision and the Module 1/3 boundary contract are both recorded before this sprint's other Epics begin | M1.0a, M1.0b |
| 4 | The risk-to-coverage calibration process is documented and owned (named owner, minimum sample size, disagreement rule) | M2.2 |
| 5 | A mutation-score baseline is recorded against the documented \~30–41% ceiling | M3.4 |
| 6 | The self-verification gate is demonstrably enforced independent of Temporal's (inactive) presence | M4.3 |
| 7 | The escalation-threshold calibration process is documented and owned; M5.1's eval suite passes identically against the real retrieval path as it did against M5.0's fake one | M5.3, M5.4 |
| 8 | The go/no-go brief visibly surfaces waived-defect rationale as a completion criterion, not an incidental side effect | M6.2 |
| 9 | Every returned answer carries a citation to a specific entity ID; the retrieval-precision baseline is recorded and reviewed before any reranker is adopted | M7P.2, M7P.3 |
| 10 | The validation-spike outcome — proceed AI-Augmented, or re-scope to Human-Only — is recorded before M8.1 begins | M8.0 |
| 11 | Every module's own Definition of Done (Sprints 1–10) still holds under integrated load; the Demo Scope Freeze's full "What V1 contains" list is demonstrable in one continuous run (made checkable item-by-item in Part 9) | IH.1–IH.5 |

## **8.4 The dependency-bump gate, named explicitly**

§1.4 and Rule A3 state the rule; this names exactly where it fires. DSPy backs the rubric-scored signature each of M1.1 (Sprint 3), M2.1 (Sprint 4), and M5.1 (Sprint 7) outputs — every module producing a calibrated classification. LangGraph is stood up at F6 (Sprint 0) and gains its self-verification rule at M4.3 (Sprint 6); every orchestrated module (1–6, 8) runs inside it without importing it directly (Final Architecture §3, "modules hand results back through the orchestrator, never directly to each other"). A version bump to either package, in any sprint, re-runs the full evaluation suite for every Epic depending on it as a merge gate — not only the sprint that first introduced the dependency. This is what keeps a silent compiled-prompt drift (AI Engineering Audit) from passing review as if it were a no-op version bump.

## **8.5 The ownership gate, generalized from §7.4**

§7.4 states this precisely for `packages/schemas` because it is the highest-blast-radius file in the repository. The same mechanism — mechanical checks first, Human-Owned review last, enforced by branch protection scoped to the folder paths in §7.1, never by asking a reviewer to remember — applies to every Human-Owned package named in §7.3: `kg-client`, `connector-contract`'s interface, `llm-gateway-client`, `config-service`, the eval-harness wiring itself, the schema-migration/compatibility-check harness, the threat-model/red-team authorship, and the LangGraph orchestration skeleton. A consuming Epic's AI coding session may propose a change to any of these as a diff; it merges only after the owning team named in Part 5, column 2 reviews it — never on §8.1's first seven rows passing alone.

## **8.6 The generated-code gate, restated from §7.5**

Both codegen pipelines' drift checks are §8.1 gates, not a separate mechanism: the `packages/schemas → TypeScript` pipeline's atomicity is "Schemas synchronized"; the connector `OpenAPI → Pydantic` pipeline's atomicity (M10.6, scoped to Module 10 only) is part of "No dependency drift." A PR that hand-edits either generated tree, rather than regenerating from the source model or spec, fails on drift — the same gate that catches a stale version pin, not a new one.

## **8.7 Known deprecated-API list**

The living reference the "No deprecated APIs" gate checks against. Additive, not exhaustive — a newly-discovered deprecation is added here (or, once IH.6's tracker is live, logged there and reflected back here) at the sprint retrospective that finds it, never silently worked around inside a single Epic's own code:

| Stale pattern | Correct target | Source |
| ----- | ----- | ----- |
| `langgraph.prebuilt` imports | `langchain.agents` | Technology Audit; Dependency Audit #6 |
| `datamodel-code-generator` used in the schemas→TypeScript direction | `quicktype`, fed by `.model_json_schema()` | Technology Audit; Accepted Change #13 |
| Neo4j CalVer rolling releases (`2026.MM.0`-style) | 5.26.x Enterprise LTS line | Technology Audit; Rule A9 |
| Langfuse self-hosted v4 | Self-hosted platform ≥3.125.0 (v3 line) | Technology Audit |
| Raw provider SDK imports (`anthropic`, `openai`) outside `packages/llm-gateway-client` | `packages/llm-gateway-client` | Rule A5; Dependency Audit #2 |
| `neo4j` driver major 6.x resolved transitively via `graphiti-core` | `neo4j` driver 5.28.x, pinned explicitly | Dependency Audit #3 |

## **8.8 Gate-failure routing**

A failure on §8.1's first seven rows is the committing Epic's own team's problem, surfaced in their own PR — no escalation needed. A failure on the eighth row (ownership) routes to the owning team named in Part 5, column 2, per F13's on-call model where the package is a foundation-layer service, or to the named team lead otherwise. An ownership-gate failure is never resolved by re-scoping the PR to route around the owning folder — the fix is the owning team's review, not a workaround.

---

# **Part 9 — Demo Milestones**

## **9.1 Two workflows, one script**

Part 2 already states a demo milestone once per sprint; repeating those verbatim here would be noise, not synthesis. Part 9 exists to assemble those eleven individual milestones into the two workflows the Data Flow (Final Architecture §5) and the Demo Scope Freeze actually name — the primary eight-step reasoning chain and the secondary production-feedback workflow — and to make the Demo Scope Freeze's own "What Version 1 contains" list checkable item by item, sprint by sprint, rather than asserted once at Sprint 11 and taken on faith until then.

## **9.2 The primary eight-step chain, mapped to sprints**

Each data-flow stage in Final Architecture §5 becomes demonstrable at exactly one sprint — the same sprint that builds the module owning that stage, per §1.1's sprint-equals-module-boundary rule:

| Step | Data-flow stage | Owning module | First demonstrable at | Demo-milestone Epic(s) |
| ----- | ----- | ----- | ----- | ----- |
| 1 | Ingestion | Module 10 | Sprint 1 | M10.1–M10.3 |
| 2 | Requirement reasoning | Module 1 | Sprint 3 | M1.1, M1.2 |
| 3 | Risk reasoning | Module 2 | Sprint 4 | M2.1 |
| 4 | Test design | Module 3 | Sprint 5 | M3.1–M3.3 |
| 5 | Execution | Module 4 | Sprint 6 | M4.1–M4.3 |
| 6 | Defect reasoning | Module 5 | Sprint 7 | M5.1, M5.2 |
| 7 | Release reasoning | Module 6 | Sprint 8 | M6.1, M6.3 |
| 8 | Knowledge query | Module 7 (surface) | Sprint 9 | M7P.1, M7P.2 |

Each step is independently demonstrable at its own sprint (Part 2's per-sprint milestones) against synthetic or partially-real upstream data; the chain is demonstrable *end to end*, all eight steps against the same ticket, only once every step exists — which is IH.2's job (Sprint 11), not any earlier sprint's.

## **9.3 The secondary feedback-loop workflow**

| Step | Data-flow stage | Owning module | First demonstrable at | Demo-milestone Epic(s) |
| ----- | ----- | ----- | ----- | ----- |
| 1 | Feedback and learning | Module 8 | Sprint 10 | M8.1, M8.2 |

The secondary workflow is one step, not eight, and its "closes the loop" claim specifically means a captured Production Incident updates the Risk Assessment Record a *future* Requirement will read (Step 3 of the primary chain) — the loop's closure is demonstrated by re-running Steps 2–3 against the affected component after Sprint 10, not by Sprint 10 in isolation. IH.2 rehearses this explicitly, per Part 2's Sprint 11 objectives.

## **9.4 Demo Scope Freeze coverage**

Every item in the Freeze's "What Version 1 contains" list, mapped to the sprint that first makes it real, so Sprint 11's Definition of Done ("the Demo Scope Freeze's full list is demonstrable in one continuous run") is a checklist, not an assertion. The Freeze's own cost-governance/DR/on-call/threat-model bullet bundles four distinct deliverables into one line; it is split into four rows below for the same reason Part 3 split Foundation into fourteen Epics rather than leaving it as one line — precision at the point something is actually verified:

| Demo Scope Freeze item | First real at | Confirmed under integrated load at |
| ----- | ----- | ----- |
| All ten product modules, per their own Definitions of Done | Sprints 1–10 (one per sprint, §1.1) | Sprint 11 (IH.2) |
| The full ten-entity data model, incl. Waived/Accepted Defect \+ Rationale attribute | Sprint 2 (M7S.1, schema); Sprint 7 (M5.2, populated); Sprint 8 (M6.2, surfaced) | Sprint 11 (IH.2) |
| The full primary eight-step chain \+ secondary feedback workflow | Assembled across Sprints 1–10 (§9.2–9.3) | Sprint 11 (IH.2) |
| Four connector adapters (Jira, GitHub, Slack, Playwright), real and demo-ready | Sprint 1 (M10.1–M10.4) | Sprint 11 (IH.2) |
| Neo4j KG with `tenant_id` scoping enforced; native timestamps standing in for Graphiti | Sprint 0 (F2, stub); Sprint 2 (M7S.2, real enforcement) | Enforced continuously from Sprint 2 onward (lint/CI, ADR-011) — not a distinct Sprint 11 event |
| LangGraph-checkpointed orchestration; Temporal scaffolded, not deployed | Sprint 0 (F6); Sprint 6 (M4.4, scaffold) | Sprint 11 (IH.2) |
| Managed Langfuse (or OTel export) during internal build | Sprint 0 (F10) | Sprint 11 (IH.5, exercised against a simulated incident) |
| One mutation-testing engine (Stryker) | Sprint 5 (M3.2) | Continues as a per-PR CI gate on Module 3 (M3.4) — not a distinct Sprint 11 event |
| WorkOS tenant provisioning; live SSO/SCIM staged to onboarding | Sprint 0 (F4) | Exercised implicitly via IH.2's rehearsal (every request authenticates); live per-partner configuration remains a post-V1 onboarding action |
| Per-tenant LLM cost ceiling | Sprint 0 (F5) | Sprint 11 (IH.4, fail-closed load test) |
| Backup/DR policy (graph \+ object storage) | Sprint 0 (F11, own recovery drill) | Validated at creation — not separately re-tested at Sprint 11 |
| On-call rotation (foundation-layer services) | Sprint 0 (F13) | Sprint 11 (IH.5) |
| Indirect-prompt-injection threat model \+ red-team suite | Sprint 0 (F12) | Sprint 11 (IH.3, finalized against the fully assembled chain) |
| Flat object-storage retention window | Sprint 0 (F11) | Validated at creation; tiering remains a named post-V1 ("V1.1") trigger, not V1 scope |
| Neo4j native hybrid/vector search, no dedicated reranker | Sprint 9 (M7P.1; M7P.3 baseline) | Sprint 11 (IH.2) |

Every row's second column already exists somewhere in Parts 2–7; this table's contribution is collecting them against the Freeze's own list, so nothing on it is left unaccounted for at Sprint 11 sign-off.

## **9.5 What's never invisible**

§1.5 states the principle for Sprint 0 specifically, the hardest sprint to make visible. Restated once, briefly, because "no invisible infrastructure-only sprint" is a standing requirement, not a Sprint-0-only concern: Sprint 0's milestone is a synthetic ticket visibly reaching the Command Center shell through real (if stub) wiring — infrastructure made visible by routing something through it, not merely declared complete. Every sprint from 1 onward inherits this by construction: each one is a module's own Definition of Done, which is itself already a working, demonstrable capability (Part 2) — there is no sprint on this roadmap whose milestone is "the code compiles," because module-equals-sprint (§1.1) means every sprint boundary is also a capability boundary.

## **9.6 Demo script repeatability**

IH.2 (Sprint 11) is where the individually-proven sprint milestones become one rehearsed, repeatable run — the artifact it produces (a demo recording/runbook, Part 3) is what makes "Demo Complete" a reproducible state the team can show a design partner twice, not a one-time live assembly. Phase 3 does not redesign this script or re-derive which steps it contains — §9.2–9.4 above are complete — it only decomposes the Epics that build toward each step into the atomic units that make that step real (Part 10).

---

# **Part 10 — Phase 3 Inputs**

Everything below is what Phase 3 (Atomic Task Planning) should take as given, inherited fact — not a research question, not a redesign opportunity, and not something the next conversation needs to re-derive. No Features, Components, Atomic Implementation Units, or literal prompts are generated here; this is the state Phase 3 starts from, in the same spirit the Implementation Audit's own "Phase 2 Inputs" section handed off to this document.

## **10.1 On document authority, extended to three**

The standing rule stated at this document's own opening (line 16) — only `Engineering_Freeze_v1.0.md` and `Implementation_Audit.md` are ever pasted into an AI coding agent's context as a statement of current fact — now extends to a third document: `Sprint_Architecture.md` itself. Phase 3 pastes all three, and only these three, into any implementation prompt or AI coding session's context. `Engineering_Landscape_Report.md` and `Development_Master_Plan.md` remain history, consulted for reasoning only, never for current-state fact — unchanged from Rule A1.

## **10.2 A terminology bridge Phase 3 needs, stated once**

The Freeze's own Deferred Decisions table defers several items "to Phase 2" — concrete API contracts, literal database schema, connector-adapter implementation detail, prompt content and each module's specific evaluation dataset. This document is Phase 2, by its own subtitle, and the Implementation Audit's own handoff section is explicitly titled "Phase 2 Inputs" addressed to it. But this document's own opening states plainly what it does *not* do: "literal schema/API-contract authoring" and "prompt generation" are named as **Phase 3** scope, not this document's own. The two source documents were written before the sprint-planning-versus-atomic-task-planning split existed as two separate phases; their "Phase 2" cross-references point to work this document deliberately did not do. **Phase 3 should read every "Phase 2" reference in `Engineering_Freeze_v1.0.md` and `Implementation_Audit.md` as pointing to itself** — a numbering artifact of how those two documents were written, not a claim that `Sprint_Architecture.md` already discharged that work.

## **10.3 What Phase 3 inherits and never reconsiders**

Everything the Freeze's own HANDOFF section says the Sprint Planner must never re-open (any module boundary; any entity in the ten-entity data model; the V1/Phase-2+ scope cut; the agent/human responsibility split and its three human-in-the-loop gates; Neo4j as the graph database; buying, not building, authentication; the build order) remains equally closed to Phase 3 — inherited a level further down, not reopened because a new document exists. Phase 3 additionally never reconsiders anything this document itself decided at the sprint-planning layer, per §1.6's own "decide once, don't re-litigate" discipline: the twelve-sprint sequence (Part 2); Epic granularity and boundaries within a sprint (Part 3); which Epic creates and which team owns each shared package (Part 5); the prompt-numbering ranges per Epic (Part 6, though not their contents — see §10.4); the folder-ownership and merge-discipline rules (Part 7); and the verification gates themselves (Part 8). Phase 3 decomposes Epics into Features, Components, and Atomic Implementation Units — it does not redraw an Epic's boundary, reassign its owner, or invent a new Epic.

## **10.4 What Phase 3 actually does**

For every Epic in Part 3, Phase 3 produces a Feature → Component → Atomic Implementation Unit decomposition, assigns each resulting prompt a literal number from that Epic's reserved range (Part 6, §6.1's overflow rule governing what happens if ten numbers aren't enough), and authors the literal content the Freeze deferred: concrete API contracts and request/response shapes, the literal graph entity/relationship property definitions implementing the ten-entity schema (including the Waived/Accepted Defect \+ Rationale attribute's exact type and `tenant_id`'s exact Cypher enforcement mechanics), internal-to-package file layout below the package boundary Part 3 already fixed, and each module's specific prompt content and evaluation dataset. This is the literal-authoring work §10.2 clarifies is Phase 3's, not this document's.

## **10.5 Genuinely open decisions Phase 3 inherits as open, not closed**

Not everything below this document's level of resolution is Phase 3's to close either — some of it is a Sprint 3 (or later) execution-time decision, and some remains genuinely deferred past Phase 3:

* **The Claude Agent SDK scoping decision (M1.0a, option a vs. b).** This is itself a scheduled Epic — a decision made when Sprint 3 actually runs, not when Phase 3 plans it. Phase 3 should decompose M1.0a into an atomic task that *records* the decision (an ADR-numbered entry, per this document's own ADR-011/012 convention) and should not write M1.1's, M2.1's, or M5.1's literal prompts as if one option were already chosen — either write them conditionally on the decision's two branches, or sequence M1.0a's atomic task strictly before those modules' own prompt-authoring tasks.  
* **`packages/extraction`'s creating-Epic gap**, per §5.3. Phase 3 should fold its literal setup into F8's own Feature/Component decomposition — matching this document's best-supported inference — rather than inventing a new Epic to own it, or silently assuming F8's Part 3 entry already names it as an Output when it does not.  
* **The calibration values themselves** (Module 2's risk-to-coverage heuristic; Module 5's escalation-confidence threshold). M2.2 and M5.3 freeze the *process*; Phase 3 authors the config-service schema and the placeholder default required by Accepted Change #25 — provisional, explicitly not calibrated — and does not write a literal calibrated number into any atomic task or prompt. Real design-partner data, which does not exist yet, is what produces the number, at a point past Phase 3's own scope.  
* **The reranker model/library name**, deferred to its own staged-adoption trigger (Accepted Change #22). Phase 3 does not name one preemptively at the atomic-task level, even as a placeholder.  
* **Per-module model routing table contents.** The mechanism (LiteLLM, versioned config, F5) is Phase 3's to wire; the actual per-module model assignments are a cost/quality tradeoff against pricing current at implementation time, not at Phase 3 planning time — Phase 3 authors the config schema, not the table's values.

## **10.6 Required inputs Phase 3 needs that neither source document supplies**

Real team-capacity data, to convert "Sprint N" (a scoped unit of work, per Part 2's own opening) into calendar dates, and to set the Sprint 0 stub-and-swap timebox before its fallback triggers — both explicitly left as a Deferred Decision by the Freeze and restated as out of this document's scope at Part 2's opening. Where that capacity is a two-person engineering team, Phase 3's atomic-unit grain should run larger and fewer per Feature than a bigger team's would — coordination overhead across two people is lower, and Part 6's ten-prompt-per-Epic reservation was sized as "enough for most Epics," not as a target to fill.

## **10.7 Expected outputs of Phase 3**

Per Epic in Part 3: a Feature → Component → Atomic Implementation Unit breakdown; literal prompt files, numbered within that Epic's Part 6 range; literal schema, API-contract, and configuration content where Part 3 marked the literal form as not-yet-authored; and, for every LLM-driven Epic, the literal prompt content and evaluation dataset itself. No Epic boundary, ownership assignment, or dependency edge from Parts 3–8 is redrawn in the process — Phase 3's output is strictly additive detail underneath a structure this document already fixed.

## **10.8 Where Phase 3 begins**

Every Phase 3 conversation on this project should begin with: **"Given `Engineering_Freeze_v1.0.md`, `Implementation_Audit.md`, and `Sprint_Architecture.md`..."** — the same standing rule this document opened with (line 16), now naming all three documents Phase 3 inherits as settled fact.

---

# **Appendix A – Minor Corrections**

Cross-referencing Parts 1–7 against both source documents while drafting Parts 8–10 surfaced no new inconsistency beyond the one this document already discloses about itself: `packages/extraction`'s creating Epic (§5.3) is this document's own best-supported inference, not a fact restated from Part 3 the way every other Part 5 row is, since neither the Sprint 0 Epic list (F1–F14) nor the Implementation Audit's Code Ownership Matrix names an explicit creating Epic for it. That gap is carried into Part 10 (§10.5) as an open item for Phase 3 rather than resolved here, consistent with §5.3's own instruction not to quietly insert a new Epic to close it.

