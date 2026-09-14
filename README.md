# QA Operating System (QA OS)

> **An AI system that scores how risky a software requirement is, drafts test cases for it, and remembers what a human decided the next time something similar comes up.**

- **Live Platform & Companion Site:** [qa.buildwithdaksh.com](https://qa.buildwithdaksh.com)
- **Author:** Daksh Chauhan ([buildwithdaksh.com](https://buildwithdaksh.com))
- **License:** MIT

---

## Monorepo Overview

This unified repository contains the complete QA OS project across its engineering codebase, companion showcase platform, and visual architecture assets:

```
qa-operating-system/
├── QA_Operating_System/     The core backend, specification library, and Next.js Command Center
│   ├── docs/                5,200+ line specification library (domain model, engineering spec, research)
│   ├── src/                 Monorepo implementation (FastAPI, uv workspace, 10 modules, packages, apps/web)
│   ├── README.md            Detailed codebase documentation, run instructions, and module ledger
│   ├── VISION.md            First-principles problem analysis & full 10-module lifecycle
│   └── GUIDANCE.md          Engineering principles & contribution guide for 4 personas
│
├── qa-os-site/              The dedicated product companion site (Next.js 14, Tailwind)
│   ├── src/                 Site pages: Architecture, Implementation, Roadmap, Run it, Collaborate
│   └── README.md            Run and deployment instructions for qa.buildwithdaksh.com
│
├── qa-os-visuals/           Standalone SVG architecture diagrams & visual assets
│   ├── qaos_architecture.svg
│   ├── qaos_overview.svg
│   └── index.html
│
└── LICENSE                  MIT License
```

---

## The Core Thesis

Software teams re-derive the same QA judgment over and over: how risky is this change, what should we test, has something like this broken before. That reasoning usually lives in a person's head, a Slack thread, or a closed ticket — and it evaporates the moment that person moves on.

QA OS absorbs the repetitive part of that reasoning (drafting risk scores and candidate test suites) while keeping humans as the sovereign decision gate (approving/rejecting candidate suites) — and, critically, persists what was decided so the next similar requirement inherits organizational memory.

### The 5-Step Working Loop (Verified End-to-End Today)

1. **Requirement In** — A requirement enters the system in plain English.
2. **Risk Scored (AI)** — Prior specs are retrieved via TF-IDF; risk is scored (0–1) with structured Pydantic extraction.
3. **Tests Drafted (AI)** — Candidate test cases are synthesized from the risk score and isolated as `draft`.
4. **Human Review Gate** — A QA lead approves, amends, or rejects each draft. Zero AI in this step.
5. **Decision Remembered** — The human decision persists to storage, compounding organizational memory.

---

## What Is Real vs. Target Architecture

We believe in complete transparency about what runs today versus what is part of the larger architectural blueprint:

- **Verified Working Slice (Modules 1, 2, 3):** Fully wired end-to-end over real HTTP routes with Pydantic validation, swappable persistence (in-memory or SQLite), and real token/cost accounting.
- **Partial Modules (Modules 5, 6, 10):** Real core logic (Defect Triage, Release Readiness, Jira connector adapter) implemented but currently sitting behind unwired routes.
- **Target Architecture & Stubs (Modules 4, 7, 8, 9):** Defined in the specification library and scheduled for collaborative implementation (distributed execution, temporal graph engine, production telemetry feedback).

For the full module-by-module audit and ledger, see [`QA_Operating_System/README.md`](./QA_Operating_System/README.md).

---

## Quick Start

### 1. Backend Core & Command Center
```bash
cd QA_Operating_System/src/services/api
uv sync
export LITELLM_BASE_URL=https://api.openai.com/v1
export LITELLM_API_KEY=sk-...
uv run uvicorn main:app --reload
```
Check health: `curl http://localhost:8000/health`

### 2. Product Companion Site
```bash
cd qa-os-site
npm install
npm run dev
```

---

## Contributing & Collaboration

If you are an applied AI engineer, QA infrastructure lead, or systems engineer interested in building robust quality architecture, see [`QA_Operating_System/GUIDANCE.md`](./QA_Operating_System/GUIDANCE.md) or visit [qa.buildwithdaksh.com/#collaborate](https://qa.buildwithdaksh.com/#collaborate).
