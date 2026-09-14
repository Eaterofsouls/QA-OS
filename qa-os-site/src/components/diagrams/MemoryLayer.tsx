import { StatusTag } from "@/components/StatusTag";

const today = [
  "TF-IDF cosine similarity over stored requirement text — stdlib Python, no embedding model, no external dependency.",
  "Top-3 matches per tenant, at or above a 0.2 similarity threshold — tuned to favor precision over recall.",
  "Injects each match's real stored risk level and real human review decision as few-shot context.",
  "Scoped to Module 1's risk-assessment prompt only — test generation doesn't use retrieval yet.",
  "Process-memory by default; survives a restart when KG_SQLITE_PATH is set.",
];

const vision = [
  "Embeddings-based semantic similarity, not just token overlap — catches paraphrases that share no vocabulary.",
  "A real knowledge graph: requirements, defects, incidents, and code changes linked as first-class relationships, not inferred from property names.",
  "Org-specific weighting — a team's own severity conventions and known-risky areas shape retrieval, not just similarity score.",
  "Retrieval extended to test generation and, eventually, defect triage — not just risk assessment.",
];

/**
 * Diagram 4 — Knowledge/Memory Layer, Today vs Vision. Uses the
 * IMPLEMENTED/VISION status colors directly, per master spec §7: "the
 * clearest place on the site for that color pairing to do real work."
 */
export function MemoryLayer() {
  return (
    <div className="grid gap-px overflow-hidden border border-line bg-line md:grid-cols-2">
      <div className="bg-bg-elevated p-5 md:p-7">
        <StatusTag status="IMPLEMENTED" />
        <p className="font-display mt-3 text-[22px] text-ink md:text-[26px]">
          Today
        </p>
        <ul className="mt-5 space-y-4">
          {today.map((line, i) => (
            <li key={i} className="flex gap-3">
              <span
                className="mt-[7px] h-[5px] w-[5px] flex-shrink-0 bg-status-implemented"
                aria-hidden="true"
              />
              <span className="font-sans text-[14px] leading-relaxed text-ink-muted">
                {line}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-bg-elevated p-5 md:p-7">
        <StatusTag status="VISION" />
        <p className="font-display mt-3 text-[22px] text-ink md:text-[26px]">
          Vision
        </p>
        <ul className="mt-5 space-y-4">
          {vision.map((line, i) => (
            <li key={i} className="flex gap-3">
              <span
                className="mt-[7px] h-[5px] w-[5px] flex-shrink-0 bg-status-vision"
                aria-hidden="true"
              />
              <span className="font-sans text-[14px] leading-relaxed text-ink-muted">
                {line}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
