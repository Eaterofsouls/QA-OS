// Single source of truth for the 10-module status ledger.
// Every diagram and table on the site derives its status coloring from this
// file, so the visual system can never silently drift out of sync with the
// documented state of the repository (README.md §6, Aug 2026 engineering pass).

export type Status = "IMPLEMENTED" | "PARTIAL" | "PLANNED" | "VISION";

export interface ModuleEntry {
  id: number;
  name: string;
  short: string;
  purpose: string;
  status: Status;
  detail: string;
  route: string;
}

export const modules: ModuleEntry[] = [
  {
    id: 1,
    name: "Requirement Risk Assessor",
    short: "Risk Assessor",
    purpose: "Scores how risky a requirement is before a single test is written.",
    status: "IMPLEMENTED",
    detail:
      "Real LLM call, real Pydantic-validated I/O, real knowledge-graph persistence. Before building its prompt it pulls the top-3 similar past requirements for the tenant (TF-IDF cosine similarity ≥ 0.2, stdlib-only — no embedding model) and injects their real stored risk level and real human review decision as few-shot context. This is retrieval-augmented prompting, not fine-tuning — no model weights change anywhere in this system.",
    route: "POST /requirements/{id}/assess",
  },
  {
    id: 2,
    name: "Test Suite Generator",
    short: "Test Generator",
    purpose: "Turns a requirement and its risk assessment into candidate test cases.",
    status: "IMPLEMENTED",
    detail:
      "Reads the risk assessment back from the knowledge graph — not resent by the client — then makes a real LLM call to generate test cases (title, steps, expected result, priority), persisted with status “draft.” Does not yet use retrieval memory itself; only Module 1's prompt does.",
    route: "POST /requirements/{id}/generate-tests",
  },
  {
    id: 3,
    name: "Review Gate",
    short: "Review Gate",
    purpose: "The human checkpoint before a generated test counts as real.",
    status: "IMPLEMENTED",
    detail:
      "A real human approve/reject decision, persisted to the same TestCase node, feeding straight back into Module 1's memory loop for the next similar requirement. No LLM call happens on this route at all — it was exercised completely unmocked, over real HTTP.",
    route: "GET /requirements/{id}/tests · POST .../review",
  },
  {
    id: 4,
    name: "Execution Orchestrator",
    short: "Execution",
    purpose: "Runs generated tests via Playwright, orchestrated through Temporal.",
    status: "PLANNED",
    detail:
      "Still in the repository, and still broken — on purpose kept, not deleted, so the gap is visible instead of hidden. It hardcodes a passing result for every test regardless of outcome, and has an unresolved bug (a NameError from a missing import). Temporal is fully provisioned in the infrastructure config; the workflow logic itself still needs to be written for real. Nothing downstream of execution should be trusted until this module is real — it's the top item on the roadmap for exactly that reason.",
    route: "exists in the repo — broken, not wired",
  },
  {
    id: 5,
    name: "Defect Triage",
    short: "Defect Triage",
    purpose: "Classifies defects using knowledge-graph context.",
    status: "PARTIAL",
    detail:
      "Real Pydantic schemas and real async logic, structurally sound — not wired to any API route yet. The fastest legitimate next win: connect it the same way modules 1–3 were connected.",
    route: "not wired",
  },
  {
    id: 6,
    name: "Release Readiness Advisor",
    short: "Readiness",
    purpose: "Produces a go/no-go recommendation, never an autonomous release trigger.",
    status: "PARTIAL",
    detail:
      "Same tier as Module 5 — real schemas and logic sitting behind no route. Its report generator file is empty.",
    route: "not wired",
  },
  {
    id: 7,
    name: "Knowledge Graph Query Surface",
    short: "KG Query",
    purpose: "Natural-language queries over the knowledge graph.",
    status: "PLANNED",
    detail:
      "Explicitly commented as a stub in its own source. It calls a hardcoded placeholder root id that nothing in the graph ever actually creates, so even the real traversal logic underneath it has nothing to find.",
    route: "not wired",
  },
  {
    id: 8,
    name: "Production Feedback Loop",
    short: "Feedback Loop",
    purpose: "Feeds production telemetry back into risk scoring.",
    status: "PLANNED",
    detail:
      "Has some real shape, but no real telemetry ingestion exists anywhere yet to feed it. Structurally premature before Module 4 is real — see the roadmap.",
    route: "not wired",
  },
  {
    id: 9,
    name: "QA Command Center",
    short: "Command Center BE",
    purpose: "Serves the dashboard's backend surface.",
    status: "PLANNED",
    detail:
      "Zero routes — a bare router with nothing registered. The command-center backend file is empty. (The real Next.js frontend you're using right now talks directly to services/api, not to this module.)",
    route: "not wired",
  },
  {
    id: 10,
    name: "Integration & Extensibility Layer",
    short: "Connectors",
    purpose: "Wires external tools — Jira, GitHub, Slack, Playwright — into the pipeline.",
    status: "PARTIAL",
    detail:
      "The Jira adapter is genuinely production-quality: real Basic Auth, real ticket translation, ~370 lines of real logic — the only connector that is. The GitHub, Slack, and Playwright adapters are still in the repository too, exactly as they are: one-line stub classes with no real logic behind them. None of the four are called from any live route yet. The Connector protocol itself, and its genuinely thorough test suite, is the real foundation here — the stubs exist to show the shape the next three adapters need to fill, not to pretend they're already filled.",
    route: "not wired",
  },
];

export const moduleCountSummary = {
  implemented: modules.filter((m) => m.status === "IMPLEMENTED").length,
  partial: modules.filter((m) => m.status === "PARTIAL").length,
  planned: modules.filter((m) => m.status === "PLANNED").length,
  total: modules.length,
};

export const statusLabel: Record<Status, string> = {
  IMPLEMENTED: "Implemented",
  PARTIAL: "Partial",
  PLANNED: "Planned",
  VISION: "Vision",
};

export const statusColorVar: Record<Status, string> = {
  IMPLEMENTED: "text-status-implemented",
  PARTIAL: "text-status-partial",
  PLANNED: "text-status-planned",
  VISION: "text-status-vision",
};

export const statusBgVar: Record<Status, string> = {
  IMPLEMENTED: "bg-status-implemented",
  PARTIAL: "bg-status-partial",
  PLANNED: "bg-status-planned",
  VISION: "bg-status-vision",
};

export const statusBorderVar: Record<Status, string> = {
  IMPLEMENTED: "border-status-implemented",
  PARTIAL: "border-status-partial",
  PLANNED: "border-status-planned",
  VISION: "border-status-vision",
};
