# Scope Decisions — How We Got to the Frozen Spec

> **Status: historical reasoning, still valid as reasoning.** This explains
> *why* the 10-module design in `02_engineering_spec.md` looks the way it
> does. It's accurate as a record of that design decision — it does not
> claim any of it is built. Only 3 of the 10 modules exist as real code today;
> see the top-level `README.md` for current status.

This is the history behind `02_engineering_spec.md`, not a spec in its own
right. It records: how the 10-module architecture was validated against three
professional personas (QA Engineer, QA Lead, CTO), what changed as a result,
what was deliberately deferred and why, and what's still an open question
going into implementation. Read `02_engineering_spec.md` for the current
architecture — come here only if you want the reasoning behind it.

*(Note: an earlier draft, `AI_QA_OS_Architecture_Spec_v1`, fed into this
validation pass and is fully superseded by it and by the Engineering Freeze.
Its content isn't reproduced here — everything in it that survived is now
part of `02_engineering_spec.md`.)*

---

## 1. How the architecture was validated

The draft architecture was pressure-tested by walking through it from three
points of view: a QA Engineer, a QA Lead, and a CTO/engineering leader — each
asking the specific questions that person would actually ask, including "is
this exactly what it looks like, or would I stop trusting it at some point?"

**Worth being upfront about:** this was one reasoning process checking its
own output, not outside validation by a real QA professional with no stake in
the pipeline. It surfaced real gaps (below), which is evidence it wasn't a
rubber-stamp — but it's not a substitute for a real design partner pushing
back on it, and that limitation is carried into the design-partner materials
themselves (§4 below).

**What the walkthrough found, net:**
- Three genuine architecture strengths held up under scrutiny and are now
  treated as settled: the Defect-vs-Flake triage requiring real Knowledge
  Graph context (not just logs), the human-review gate before any AI-drafted
  test ships, and the hard rule that an agent's own test run is never sole
  verification ground truth for its own change.
- Four real gaps were found (not just communication issues) and are logged
  below as open items — most importantly, the release-readiness data model
  is missing a "Waived/Accepted Defect + Rationale" field, without which the
  product can't actually deliver on one of its own stated differentiators.
- A few findings were communication problems, not architecture problems —
  e.g. "Module 9 eliminates context-switching" overstated what V1 evidence
  actually supports — and were fixed by rewording the design-partner
  materials, not by changing the architecture.

## 2. Scope confirmations

All 10 modules' V1-core vs. Phase-2+ classification from the architecture
draft were confirmed unchanged by the validation pass. Two things changed
during validation, and only two:

1. **Module 2 (Risk & Test Strategy)** — its Sprint 2 completion criteria now
   explicitly state that the risk-to-coverage-depth heuristic is
   **provisional**, calibrated jointly with each design partner's QA lead
   during pilot use — because no source in the research pipeline validates
   that heuristic yet (see open items below). Module 2 stays V1-core; this
   only changes what "done" means for it.
2. **Environment & Data Strategy's Phase 2+ deferral** is now explicitly
   named to design partners (§4 below) instead of being an undisclosed gap.
   It was independently confirmed as the single most severe, least-addressed
   pain point across the whole research program *and* the Rank 2 uncontested
   competitive differentiator — deferring it was a deliberate bet (ship the
   harder-to-build judgment layer first, since environment orchestration
   already has point solutions in the market), not an oversight, but it
   needed to be said out loud rather than left implicit.

No module was pulled forward or cut. Pulling Environment & Data forward was
considered and rejected — it would require Foundation-layer schema work,
which is explicitly the single most expensive mistake this plan can make if
done prematurely, and would pull engineering time away from the layers where
the actual competitive moat lives.

## 3. Open items for future work

Carried forward, not yet resolved — these are the seed backlog for
post-freeze work, not things `02_engineering_spec.md` already accounts for:

1. **[Highest priority]** Release Readiness / Defect Report needs an explicit
   "Waived/Accepted Defect + Rationale" data-model attribute — without it the
   product can't back its own differentiator claim against standard release
   notes. Needs a data-model revision pass, not new research.
2. Module 1's ambiguity-detection checklist needs to be explicitly specified
   as built from validated gap-taxonomies (missing error-handling branches,
   missing interaction with adjacent features — both independently confirmed
   in the tooling/artifact research) rather than generic completeness rules.
   This is the literal mechanism behind the product's strongest demo moment,
   so it matters more than it looks like it should.
3. Module 7's natural-language query interface should be required to cite
   the specific record it drew an answer from, not just produce fluent
   prose — a "legible, not opaque" positioning gap.
4. No source anywhere quantifies whether AI-drafted test steps net out to
   *less* review/maintenance time overall, given real-world LLM-generated
   tests cap out around 30–40% mutation score. Treat as an open empirical
   question to measure during pilot use, not an assumption either way.
5. Risk-to-coverage-volume conversion and execution-prioritization heuristics
   (feeding Module 2) still need to be designed and calibrated against a
   real design partner's QA-lead judgment before they're more than
   provisional.
6. Incident Action-Item Extraction's AI-Augmented classification (Module 8)
   was never run through the formal transformability-classification process
   used elsewhere — needs validation before implementation.
7. Full Action-Item → ADR/Test-Case auto-generation (a richer version of the
   Module 8 learning loop) is Phase 2+ and needs its own pass once the
   narrower V1 loop-closure is in production and its value can be measured.
8. No confirmed artifact/entity for test-data or environment provisioning
   requests yet — relevant whenever that layer eventually gets built.
9. The cost of running the full feedback-to-learning loop is unquantified —
   relevant to how much Phase 2+ investment it deserves.
10. Whether the Nygard ADR template sees real adoption specifically within QA
    teams (vs. architecture teams generally) is still an open question that
    affects how reliable the ADR entity is as a populated knowledge source
    early on.

## 4. Design partner summary

This is the plain-language version of the above — no process vocabulary, no
provenance tags — written to stand alone for someone evaluating the product
directly.

**What it does, in one flow:** reads a real requirement → flags specific
missing acceptance criteria (not a grammar check) → scores risk and states a
coverage depth with a one-sentence reason tied to real history → generates
editable functional/boundary test cases → runs them live via Playwright →
classifies a failure as a real defect, a flake, or an environment issue with
its evidence shown → produces a release recommendation that's visibly built
from everything before it, not asserted from nowhere → answers plain-language
questions like "why did we test this?" grounded in its own accumulated
history.

**What's intentionally unfinished, and why:**
- **Integration breadth:** launching with Jira, GitHub, Slack, and Playwright
  only — not broad tool coverage.
- **Deep historical memory:** the system starts thin on day one; it needs
  real usage with your team to build compounding insight. Said upfront, not
  oversold.
- **Production feedback depth:** relies on manual incident input or a single
  monitoring integration; updates risk models but doesn't yet auto-generate
  new test cases from an incident.
- **Enterprise administration:** enterprise-grade admin, advanced security
  config, and multi-tenant scaling are deferred until core value is proven.
- **Autonomous release triggering:** the system recommends go/no-go; it will
  not auto-trigger a release without a human, until you tell us you trust it
  enough to.
- **Environment & Data Strategy:** not shipped in this version. Our own
  research confirms this is currently the most painful, least-addressed
  problem in QA tooling generally — we're sequencing the judgment layer
  first because it's the harder thing to build credibly and the thing we
  believe nobody else is doing at all. This is a bet on what to prove first,
  not a blind spot we missed.

**Questions worth asking a design partner directly:**
- Does the risk score and reasoning match what you'd independently conclude
  as a QA lead? Where does it diverge, and why?
- Would you make the same go/no-go call under pressure, based on what the
  release-readiness brief shows you?
- At what specific step did you stop trusting the system's output? What
  would win that trust back?
- Run your messiest recent ticket — not ours — through requirement
  gap-detection. Does it catch what a senior engineer on your team would
  catch, or does it feel generic?
- Of everything intentionally left unfinished (including environment/data
  orchestration), what's an actual dealbreaker for your team versus a
  nice-to-have?
- What would it take to trust the system enough to let it auto-trigger a
  release on a low-stakes deployment?

**One honest note:** all of this was pressure-tested by reasoning through it
from the QA engineer / QA lead / CTO points of view — including hunting for
where it would fall apart, not just where it would shine. But that was still
us testing ourselves. The real test is your team pushing on it with your own
tickets, your own defect history, and your own skepticism.
