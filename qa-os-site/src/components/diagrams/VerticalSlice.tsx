"use client";

import { useState } from "react";

const steps = [
  {
    title: "Assess",
    endpoint: "POST /requirements/{id}/assess",
    detail:
      "Module 1 scores risk with a real LLM call — informed by up to 3 similar past requirements pulled via TF-IDF retrieval, when any clear the 0.2 similarity threshold.",
  },
  {
    title: "KG persist",
    endpoint: "kg_client.upsert_node()",
    detail:
      "Requirement and RiskAssessment nodes are written to the knowledge-graph backend — in-memory, SQLite, or Neo4j, same call, zero branching at this call site.",
  },
  {
    title: "Generate tests",
    endpoint: "POST /requirements/{id}/generate-tests",
    detail:
      "Module 2 reads the risk assessment back from the KG — not resent by the client — then makes a real LLM call to draft test cases.",
  },
  {
    title: "KG persist",
    endpoint: "kg_client.upsert_node()",
    detail:
      "Generated TestCase nodes are written with status=“draft,” each linked back to its requirement.",
  },
  {
    title: "Read back",
    endpoint: "GET /requirements/{id}/tests",
    detail:
      "The frontend reads the current draft test cases and their review status straight out of the KG — no client-side cache to go stale.",
  },
  {
    title: "Human review",
    endpoint: "POST /requirements/{id}/tests/{test_case_id}/review",
    detail:
      "Module 3 — a real approve/reject decision, no LLM call at all. Exercised completely unmocked, over real HTTP.",
  },
  {
    title: "KG write",
    endpoint: "kg_client.upsert_node()",
    detail:
      "The reviewed TestCase's status, reviewer id, and note are written back — closing the loop that Module 1's retrieval memory reads from on the next similar requirement.",
  },
];

/**
 * Diagram 3 — the real vertical-slice sequence. Interactive: focusing or
 * hovering a step reveals the real endpoint/route it corresponds to, per
 * master spec §7.
 */
export function VerticalSlice() {
  const [active, setActive] = useState(0);
  const step = steps[active];

  return (
    <div className="w-full">
      <div className="flex flex-col gap-0 md:flex-row md:items-stretch md:gap-0">
        {steps.map((s, i) => (
          <div key={i} className="flex flex-1 items-center md:flex-col">
            <button
              onMouseEnter={() => setActive(i)}
              onFocus={() => setActive(i)}
              onClick={() => setActive(i)}
              className="flex w-full flex-col items-start gap-1.5 border bg-bg-elevated px-3 py-3 text-left duration-200 md:items-center md:text-center"
              style={{ borderColor: active === i ? "#000000" : "#D8D8D8" }}
              aria-pressed={active === i}
            >
              <span className="font-mono-label text-[10px] text-ink-muted">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="font-sans text-[13px] font-medium text-ink">
                {s.title}
              </span>
            </button>
            {i < steps.length - 1 && (
              <span
                className="hidden h-px flex-shrink-0 basis-4 bg-line md:block"
                aria-hidden="true"
              />
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 border-t border-line pt-5">
        <p className="font-mono-label text-[11px] text-ink-muted">
          {step.endpoint}
        </p>
        <p className="mt-2 max-w-2xl font-sans text-[14px] leading-relaxed text-ink">
          {step.detail}
        </p>
      </div>
    </div>
  );
}
