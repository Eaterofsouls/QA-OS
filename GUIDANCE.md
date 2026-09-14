# GUIDANCE.md — Engineering Principles, Roadmap Order, and How to Contribute

This document is for anyone extending this codebase: what rules the existing code actually follows (so new code doesn't quietly break them), the order the roadmap has to happen in and why, and specific, honest asks for four kinds of collaborator.

## Principles the existing code follows — keep these when you extend it

**1. Never fabricate success.** This shows up independently in at least five places in this codebase: the LLM gateway raises a real error instead of returning a fake empty success; the extraction layer raises a real error instead of returning an unvalidated guess; the similarity search returns an empty list instead of inventing a plausible-looking match; usage tracking returns `null` instead of `0` for a genuinely missing token count; cost aggregation returns `null` rather than silently undercounting when any single entry is incomplete. If you're adding a new failure path anywhere in this system, the question is always: does this return an honest empty/error, or does it quietly make something up? Only the first one is acceptable here.

**2. Isolate side effects from the primary response.** Cost-ledger logging is wrapped in its own `try/except` specifically so a disk or permissions failure in an audit log can never break a successful `/assess` or `/generate-tests` response — while a genuine LLM or parsing failure is *not* swallowed the same way. The distinction matters: a side-channel audit log failing should be loud in the logs and invisible to the caller; a primary-path failure should be loud to the caller too. Get this backwards in either direction and you've either hidden a real failure or let a logging problem take down a real feature.

**3. One interface, swappable backends, zero call-site changes.** `KGClientInterface` has three implementations (in-memory, SQLite, Neo4j) selected by a single environment variable at one factory function. If you add a fourth storage backend, or extend any other interface in this system, the test is: can every existing caller keep working with zero changes? If not, the abstraction isn't actually doing its job yet.

**4. A contract before an implementation.** The `Connector` protocol, and its generic, reusable contract-test suite, existed before any real adapter was written against it — including a fake implementation whose only purpose is exercising the contract in isolation. If you're adding a new external integration, write it against `connector-contract` and run the existing test suite against it before writing adapter-specific tests. Don't skip the contract because "this one's simple."

**5. Prove it with a test that could actually fail.** `verify_step7_sqlite_persistence.py` runs as two genuinely separate OS processes — write, full exit, then read — specifically because a same-process before/after check doesn't prove persistence survives a restart, only that Python's own memory wasn't cleared. Before writing a verification script, ask what would make it pass even if the thing you're testing were actually broken. If the answer is "plenty," it's not proof yet.

**6. When something is fake or broken, say so in the code and leave it visible.** Module 4 hardcodes a passing result for every test and has an unresolved `NameError`. It stays in the repository exactly as it is, documented in the README as broken — not deleted, not quietly patched to look more finished, not hidden behind a "coming soon" label that implies it's closer to done than it is. If you fix Module 4, update the README and this document in the same change. If you find another place where code claims to do something it doesn't, the fix is either to make it real or to label it honestly — never to make the label vaguer.

## Roadmap — ordered by real dependency, not by what's exciting to build

No dates, on purpose. The order below is load-bearing:

1. **Make Module 4 (execution) real.** Nothing past this point can be trusted until tests actually run against a real environment instead of returning a hardcoded result. This is the single highest-leverage next step in the entire codebase — everything else downstream depends on it meaning something.
2. **Wire Modules 5 and 6 in.** Their reasoning logic already exists; they need a route, and they need Module 4's real output to reason about.
3. **Build real evaluation.** Once there's real execution data, there's a real question worth answering: did a change to a prompt or a retrieval strategy make things better, or just different? `packages/evaluation` needs to exist before any specialization work is worth trusting.
4. **Only then, specialize.** Org-specific terminology, severity conventions, known-risky-area weighting — as retrieved context first, not baked into model weights. Still fully interpretable, still cheap to iterate, and now measurable against a real evaluation harness instead of vibes.
5. **Fine-tuning or preference learning, last, and narrow.** Only once there's real labeled trace volume — hundreds of real approve/reject/correct decisions per task type — and only for specific sub-tasks where retrieval and context genuinely plateau. Full-system fine-tuning stays the wrong first move for as long as steps 1 through 4 haven't happened: it's expensive, hard to debug, and it throws away the interpretability retrieval-based memory gives for free.

A concrete, currently-missing piece worth calling out on its own: feedback should be captured as more than approve/reject. When a QA lead rejects a generated test, the system doesn't yet ask *why* in structured form — wrong risk level? Missing test type? Tone mismatch with team convention? That's a real, scoped, buildable feature, not vague future work, and it would make every downstream module (especially triage and specialization) meaningfully better.

## Where I need help — four kinds of collaborator, four specific asks

This was built solo, and written up as precisely as possible about where it's real and where it's an informed guess. The guesses are exactly where I want to be told I'm wrong.

### QA Engineers & Test Architects
You've lived the actual problem this is trying to solve — the tribal knowledge, the re-derived risk assessments, the same bug rediscovered by someone new every eighteen months. **The ask:** look at Module 1's risk scoring and Module 2's generated test cases and tell me where they're wrong. Not where they're incomplete — where a real QA lead would actually disagree with the model's judgment. That feedback is worth more than another feature.

### Applied AI / LLM Engineers
The retrieval layer is deliberately simple right now — TF-IDF cosine similarity, no embeddings, no vector store — and the reasoning for that restraint is written into the code, not just the docs (see `packages/kg-client/similarity.py`). **The ask:** tell me if that restraint is still correct, or if it's time to earn the added complexity of an embedding-based retrieval layer. And if the structured-output validation around every LLM call has a hole in it I haven't found, I want to know before a real user does.

### Backend & Platform Engineers
Three of ten modules are real and wired. The other seven have a real interface contract waiting for them, a Neo4j client that's never touched a live database, and zero authentication. **The ask:** Module 4 (execution) is first on the roadmap and currently exists, broken, on purpose left visible rather than hidden. If you want to build a real Playwright/Temporal execution loop against a real interface contract, that's the single highest-leverage contribution available right now.

### Engineering Leaders piloting QA workflows
Everything in [VISION.md](./VISION.md) is informed guessing about what a real QA organization needs. It hasn't run against a real backlog, a real team, or a real on-call rotation yet. **The ask:** if you'd be willing to pilot the working slice — risk-score and generate tests for a real sprint's worth of requirements against your own review process — the gap between what I've assumed and what you'd actually need is exactly what I want to find.

No pitch deck, no call required. A direct message, an issue, or a pull request is enough.
