"use client";

type Lane = "deterministic" | "llm" | "human";

interface Step {
  label: string;
  lane: Lane;
  vision?: boolean;
}

// Lanes are distinguished by row position and label, never by hue — the
// Kononenko system's own rule (DESKTOP_AUDIT_DRAFT.md §15.12): "hierarchy is
// carried almost entirely by type scale and placement rather than color,
// since there's no accent color." A filled cell is real; a dashed, lighter
// cell is vision — the same solid-vs-dashed grammar used everywhere else on
// this site.
const laneMeta: Record<Lane, { title: string; desc: string }> = {
  deterministic: {
    title: "Deterministic logic",
    desc: "Plain code. Same input, same output, every time.",
  },
  llm: {
    title: "LLM reasoning",
    desc: "A real model call. Probabilistic — read as a draft, not a fact.",
  },
  human: {
    title: "Human sign-off",
    desc: "Nothing ships past this lane without a person deciding.",
  },
};

const steps: Step[] = [
  { label: "Requirement intake", lane: "deterministic" },
  { label: "Retrieval lookup (TF-IDF)", lane: "deterministic" },
  { label: "Risk scoring", lane: "llm" },
  { label: "Test generation", lane: "llm" },
  { label: "KG persist / read-back", lane: "deterministic" },
  { label: "Review — approve / reject", lane: "human" },
  { label: "Execution triage", lane: "llm", vision: true },
  { label: "Release readiness", lane: "llm", vision: true },
  { label: "Release sign-off", lane: "human", vision: true },
];

const lanes: Lane[] = ["deterministic", "llm", "human"];

/**
 * Diagram 5 — Reasoning Boundary. Answers "where does AI end and judgment
 * begin" at a glance. Steps marked vision=true extend the lifecycle past
 * what's built today — shown dashed/lighter, still placed in their real
 * lane. Monochrome throughout (Kononenko design system).
 */
export function ReasoningBoundary() {
  return (
    <div className="w-full overflow-x-auto">
      <div style={{ minWidth: `${steps.length * 108}px` }}>
        <div
          className="grid gap-1"
          style={{ gridTemplateColumns: `repeat(${steps.length}, minmax(0,1fr))` }}
        >
          {steps.map((s, i) => (
            <p
              key={i}
              className="px-1 pb-3 text-center font-sans text-[11px] leading-tight text-ink-muted"
            >
              {s.label}
              {s.vision && (
                <span className="ml-1 font-mono-label text-[9px] text-status-vision">
                  vision
                </span>
              )}
            </p>
          ))}
        </div>

        {lanes.map((lane) => (
          <div key={lane} className="mb-1 flex items-stretch gap-1">
            <div
              className="grid flex-1 gap-1"
              style={{
                gridTemplateColumns: `repeat(${steps.length}, minmax(0,1fr))`,
              }}
            >
              {steps.map((s, i) => {
                const filled = s.lane === lane;
                const isVision = filled && s.vision;
                return (
                  <div
                    key={i}
                    className="flex h-12 items-center justify-center border"
                    style={{
                      borderColor: filled ? (isVision ? "#8A8A8A" : "#000000") : "#D8D8D8",
                      borderStyle: isVision ? "dashed" : "solid",
                      borderWidth: filled ? "1.5px" : "1px",
                      backgroundColor: "#FFFFFF",
                    }}
                    aria-hidden="true"
                  >
                    {filled && (
                      <span
                        className="h-[6px] w-[6px]"
                        style={{ backgroundColor: isVision ? "#8A8A8A" : "#000000" }}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {lanes.map((lane) => (
          <div key={lane} className="flex items-start gap-2.5">
            <span
              className="mt-[5px] h-[8px] w-[8px] flex-shrink-0 bg-ink"
              aria-hidden="true"
            />
            <div>
              <p className="font-mono-label text-[11px] text-ink">
                {laneMeta[lane].title}
              </p>
              <p className="mt-1 font-sans text-[12px] leading-relaxed text-ink-muted">
                {laneMeta[lane].desc}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-5 border-t border-line pt-4">
        <span className="flex items-center gap-2 font-mono-label text-[10px] text-ink-muted">
          <span className="h-[10px] w-[10px] border-[1.5px] border-ink bg-white" />
          real, exercised
        </span>
        <span className="flex items-center gap-2 font-mono-label text-[10px] text-ink-muted">
          <span
            className="h-[10px] w-[10px] bg-white"
            style={{ border: "1.5px dashed #8A8A8A" }}
          />
          vision, not built
        </span>
      </div>
    </div>
  );
}
