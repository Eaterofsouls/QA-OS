import { Status } from "./modules";

export interface RoadmapNode {
  id: string;
  index: number;
  title: string;
  status: Status;
  summary: string;
  detail: string;
  dependsOn: string[];
}

export const roadmapNodes: RoadmapNode[] = [
  {
    id: "foundation",
    index: 1,
    title: "Foundation",
    status: "IMPLEMENTED",
    summary: "Done — what exists today.",
    detail:
      "Real modules 1–2–3, a real review-gate-feeds-memory loop, real persistence (in-memory and SQLite), and real error-honesty throughout the call path — no step silently fakes success.",
    dependsOn: [],
  },
  {
    id: "reliable-reasoning",
    index: 2,
    title: "Reliable QA Reasoning",
    status: "PLANNED",
    summary: "De-fake execution; add a real eval harness.",
    detail:
      "De-fake Module 4 — real test execution, not a hardcoded pass — and add an eval harness that checks module output against human-approved ground truth instead of eyeballing it. Nothing downstream of execution can be trusted until this is real.",
    dependsOn: ["foundation"],
  },
  {
    id: "wire-remaining",
    index: 3,
    title: "Wire the Remaining Real Logic",
    status: "PLANNED",
    summary: "Connect Modules 5 and 6 to real routes.",
    detail:
      "Modules 5 (Triage) and 6 (Readiness) already have real schemas and logic — connect them to routes and to the same knowledge-graph memory pattern Module 1 already uses. The lowest-risk, highest-visible-progress step available.",
    dependsOn: ["reliable-reasoning"],
  },
  {
    id: "org-context",
    index: 4,
    title: "Organization-Specific Context",
    status: "PLANNED",
    summary: "Wire the real Jira connector into the live flow.",
    detail:
      "Wire the already production-quality Jira connector into the real flow — this is what turns “a demo with typed-in requirements” into “a system that ingests a real backlog.” Requires real historical requirement and defect data from a cooperating organization to be useful, not just wired.",
    dependsOn: ["wire-remaining"],
  },
  {
    id: "deep-integrations",
    index: 5,
    title: "Deep Integrations",
    status: "VISION",
    summary: "GitHub, Playwright, and Slack, wired for real signal.",
    detail:
      "GitHub (code-change context feeding risk scoring), Playwright (real execution results feeding a now-real Module 4), Slack (surfacing review requests where QA leads already work).",
    dependsOn: ["org-context"],
  },
  {
    id: "evaluation-infra",
    index: 6,
    title: "Evaluation Infrastructure",
    status: "VISION",
    summary: "Score reasoning against human-labeled ground truth.",
    detail:
      "packages/evaluation is currently empty — this is where it earns its existence: golden-set scoring of risk assessments and generated tests against human-labeled outcomes, run on every change to the reasoning prompts, not just eyeballed.",
    dependsOn: ["deep-integrations"],
  },
  {
    id: "feedback-scale",
    index: 7,
    title: "Feedback Loops at Scale",
    status: "VISION",
    summary: "Real production telemetry feeding risk scoring.",
    detail:
      "Module 8 (Production Feedback) — real telemetry, execution outcomes, and post-release defects flowing back into risk scoring. This only becomes meaningful once Module 4 and real execution exist upstream.",
    dependsOn: ["evaluation-infra"],
  },
  {
    id: "specialization",
    index: 8,
    title: "Specialization",
    status: "VISION",
    summary: "Org-specific context first; narrow fine-tuning last.",
    detail:
      "Retrieval and context specialization per organization, evaluation-driven prompt iteration, and — only once there is enough real labeled trace volume — targeted fine-tuning of narrow sub-tasks, never the whole system.",
    dependsOn: ["feedback-scale"],
  },
  {
    id: "production-hardening",
    index: 9,
    title: "Production Hardening",
    status: "VISION",
    summary: "Auth, real graph queries at scale, cost ceilings, observability.",
    detail:
      "Auth (currently nonexistent), the Neo4j swap for real graph queries at scale, cost-ceiling enforcement (CostCeiling is still an empty stub sitting next to a real CostLedger), and observability.",
    dependsOn: ["specialization"],
  },
  {
    id: "mature-qa-os",
    index: 10,
    title: "Mature, Organization-Specific QA Intelligence",
    status: "VISION",
    summary: "The end state this roadmap is ordered toward.",
    detail:
      "The direction every arrow above points at — and, explicitly, not a claim this site is making about today. Each arrow in this roadmap is a real dependency, not a scheduling preference: feedback loops are structurally meaningless before execution is real, and specialization is premature before evaluation exists to measure whether “specialized” is actually better.",
    dependsOn: ["production-hardening"],
  },
];
