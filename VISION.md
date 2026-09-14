# VISION.md — Why This Exists, and What It's Actually Aiming At

## The problem, stated plainly

Every software team re-derives the same QA judgment, over and over, from scratch.

A requirement comes in. Someone has to decide how risky it is — is this a small UI tweak or does it touch the auth layer, the payment flow, the thing that broke production eighteen months ago? Then someone has to decide what to test. Then, eventually, someone has to decide whether it's safe to ship. All three of those decisions require judgment that lives almost entirely in people's heads — the QA lead who remembers the last time this module broke, the engineer who knows this endpoint is fragile, the person who was on call the night the session-refresh bug shipped.

That knowledge doesn't compound. It doesn't get written down in a form anyone can query. It doesn't survive a team reorg, a departure, or eighteen months of turnover. The same risk gets re-assessed from zero, the same category of test gets re-invented, and the same class of bug gets rediscovered by someone new, on a schedule of roughly "however long it takes for everyone who remembered the first time to leave."

This project's bet is narrow and specific: **an AI system can absorb the repetitive part of that reasoning — drafting a risk assessment, drafting test cases — while a human keeps the part that actually requires judgment: deciding what ships. And the system should remember every decision, so the next similar case inherits it instead of starting cold.**

That's the whole thesis. Everything below is what it takes to actually build that, and where this project currently stands against it.

## Why this is hard, specifically

It would be easy to build a demo that "does QA with AI" — feed a requirement to a model, get back some test cases, done. That's not hard, and it's also not useful, because it doesn't solve the actual problem. The actual problem is memory and trust, not text generation:

- **Memory**, because a system that re-derives every risk assessment from nothing is no better than a person doing it from nothing. The value is in remembering what happened last time — which means real retrieval, real storage, and a real mechanism for pulling relevant history into a new decision.
- **Trust**, because nobody should ship a test suite an AI wrote without a person looking at it, and nobody should trust a risk score without knowing why the system arrived at it. That means every AI output needs to be a *draft*, structurally, not a decision — with a real human gate before anything downstream depends on it.

Those two constraints shape almost every real design decision in this codebase. They're why Module 3 (the review gate) exists as a hard requirement rather than a nice-to-have, why retrieval was built before anything fancier, and why every connector in the integration layer defaults to "advisory only" at the schema level rather than by convention.

## The full lifecycle this is aiming at

The specification describes ten modules, forming one pipeline:

1. **Requirement Risk Assessor** — score how risky a requirement is, informed by what's happened with similar requirements before.
2. **Test Suite Generator** — draft test cases from the requirement and its risk profile.
3. **Review Gate** — a human approves or rejects every draft. Nothing downstream trusts an unreviewed test.
4. **Execution Orchestrator** — run the approved tests for real, against a real environment.
5. **Defect Triage** — when something fails, help figure out if it's a real regression, a flaky test, an environment issue, or a test defect — using history, not a blank slate.
6. **Release Readiness Advisor** — roll all of the above into a go/no-go recommendation for a release, with the reasoning attached, not just a verdict.
7. **Knowledge Graph Query Surface** — let a person ask, in plain language, "what happened the last time we touched this?" and get a real answer.
8. **Production Feedback Loop** — feed real production incidents back into risk scoring, so the system's sense of "risky" is grounded in what actually broke, not just what looked scary on paper.
9. **QA Command Center** — the interface a QA team actually lives in day to day.
10. **Integration & Extensibility Layer** — meet teams where they already work: Jira, GitHub, Slack, CI, whatever the real workflow is, rather than asking anyone to adopt a new tool in isolation.

Read that list as a dependency graph, not a checklist. Feedback loops (8) are structurally meaningless before execution (4) is real — there's nothing genuine to feed back yet. Release readiness (6) can't be trusted before defect triage (5) exists. Specialization of any kind is premature before evaluation exists to measure whether "specialized" is actually better than the baseline. The roadmap in [GUIDANCE.md](./GUIDANCE.md) is ordered by these real dependencies, not by which module sounds most impressive to build next.

## Where this stands today, against that vision

Three of the ten modules are real, wired, and running end-to-end: risk assessment, test generation, and the human review gate — modules 1 through 3, the exact loop described in the README's five steps. That's not an arbitrary starting point. It's the smallest slice that actually tests the thesis: can an AI system draft useful risk assessments and test cases, and can a human review-and-decide loop keep it trustworthy? Everything past that point — real execution, real triage, real production feedback — is what happens once that foundation is proven, not before.

Two more modules (defect triage, release readiness) have real reasoning logic already written, sitting behind no API route yet — a deliberate choice to write the hard part first and wire it in once execution (its prerequisite) is real. One integration adapter (Jira) is genuinely production-quality and unwired for the same reason: there's no live pipeline event to wire it into yet that would make the connection meaningful rather than decorative.

The rest — execution, KG querying, the production feedback loop, the command-center backend — are either broken (Module 4, left visibly so) or empty scaffolding. See [README.md](./README.md) for the exact, module-by-module accounting, and [GUIDANCE.md](./GUIDANCE.md) for what actually needs to happen to move each of them forward.

## Why retrieval-first, not fine-tuning-first

A reasonable question: why isn't this project training or fine-tuning a model on QA data? Three reasons, in order of how much they matter:

1. **There's no real labeled data yet.** Fine-tuning on invented or synthetic QA decisions would teach a model to imitate guesses, not judgment. Real training data — hundreds of real approve/reject/correct decisions per task type, from a real QA process — doesn't exist yet because the working slice hasn't been run against a real backlog long enough to produce it.
2. **Retrieval is cheaper, more interpretable, and easier to debug when it's wrong.** If Module 1 scores something incorrectly, you can look at exactly which past requirements it pulled as context and see why. A fine-tuned model's mistake is much harder to trace to a cause.
3. **Full-system fine-tuning would throw away the interpretability retrieval gives for free**, in exchange for a capability this project doesn't have the real data to justify yet. That's a bad trade at this stage, not a permanently bad idea — see the training/evolution plan in GUIDANCE.md for when and how that changes.

This is a considered sequencing decision, not an avoidance of "real AI work." Reach for the more complex tool once the simpler one has genuinely plateaued against real usage — not before.

## Why a human gate, structurally, not as a setting

Every AI-drafted test case ships with `status: draft`. Nothing changes that status except a human decision recorded in Module 3. This isn't a configurable safety toggle that a future version might remove for "trusted" users — it's the mechanism by which this system is allowed to be wrong without that being catastrophic. An AI that's occasionally wrong about risk scoring is useful, as long as a person is the one who decides what ships. An AI that's occasionally wrong and nobody checks is not a QA tool; it's a liability with a UI.

The same principle shows up in the integration layer's design: every external status update a connector could post defaults to `advisory_only = True` at the schema level, not by convention a future engineer might forget. Connectors translate and advise. They don't autonomously block or approve anything. That's the same judgment as the review gate, pushed one layer further out.

## What "done" looks like — and why it isn't a fixed date

There's no calendar in the roadmap on purpose. "Done" for this project isn't a ship date; it's a dependency graph fully walked: execution real, so feedback loops mean something; evaluation real, so specialization can be measured instead of guessed at; enough real usage, from a real QA team, to know whether the assumptions in this document survived contact with an actual backlog. The single biggest open question this project has is not technical — it's whether the shape of this five-step loop is actually what a real QA organization needs, or whether it's an informed guess that hasn't been pressure-tested by anyone with something real at stake. That's precisely the gap [GUIDANCE.md](./GUIDANCE.md)'s collaboration section is asking for help closing.
