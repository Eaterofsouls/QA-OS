# Specification Library — Index

This folder is the "what should this system be" answer — the target design,
not a description of what's currently built. **For what's actually real
today, read the top-level `README.md` §4–§7 first.** Only 3 of the 10 modules
described here are real, wired, working code; the rest of this library
describes where the system is headed.

| # | Doc | What it answers | Status |
|---|---|---|---|
| — | `01_domain_model.md` | How does QA work as a profession, independent of any tooling? | Reference — not build-status dependent. |
| — | `02_engineering_spec.md` | What is this system meant to be, architecturally? | **Target architecture.** Authoritative as the design, not as current state. |
| — | `03_roadmap.md` | In what order was this meant to be built? | **Original plan, not build history** — the actual build skipped most of this sequence. See its own status note. |
| — | `05_scope_decisions.md` | Why does the target spec look like this, and what's still open? | Historical reasoning — still valid as reasoning, not as a status report. |
| — | `research/` | What's the external evidence behind these decisions? | Reference — market landscape, AI-automation feasibility, industry standards, real-world artifact formats. |

**Recommended reading order:** top-level `README.md` first (what's real).
Then `02_engineering_spec.md` if you want the full target design, then
`05_scope_decisions.md` only if you want the "why" behind a specific part of
it. `03_roadmap.md` is only useful if you're picking up work toward the
unbuilt modules. `01_domain_model.md` and `research/` are dip-in reference
material.

## `research/`

| Doc | Covers |
|---|---|
| `market_and_competitors.md` | Who else is building AI-assisted QA tooling, and where's the genuine competitive whitespace |
| `ai_automation_landscape.md` | Which QA tasks are actually automatable today vs. AI-augmented vs. human-only, and what current models can/can't reliably do |
| `standards_and_compliance.md` | ISTQB, TMMi, ISO/IEC/IEEE 29119, OWASP ASVS, WCAG — what this system's outputs need to stay fluent in |
| `artifacts_and_tooling.md` | Real-world QA document formats (test plans, defect reports, etc.) and the tooling/integration ecosystem to build against |

---

*A note on how this is organized: the research/spec process originally
produced 12 separate documents across three folders, several superseding
each other, with process metadata (session/hop tags, `[SOURCE:]` /
`[SYNTHESIS:]` markers) baked into the prose, plus a full per-task backlog
(`Atomic_Task_Map_Final.md`) scoped to a 10-module, 12-sprint build that was
never carried out — the actual implementation is a much smaller, 3-module
slice built by hardening existing scaffolding directly. That backlog has been
removed rather than kept as dead weight; this library was consolidated,
trimmed of process scaffolding, and given plain names, with each doc's status
(target design vs. reference vs. history) stated explicitly rather than
implied.*

