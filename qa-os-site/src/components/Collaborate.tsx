import { site } from "@/lib/site";

interface Persona {
  role: string;
  forWhom: string;
  ask: string;
}

const personas: Persona[] = [
  {
    role: "QA Engineers & Test Architects",
    forWhom:
      "You've lived the actual problem this is trying to solve — the tribal knowledge, the re-derived risk assessments, the same bug rediscovered by someone new every eighteen months.",
    ask: "Look at Module 1's risk scoring and Module 2's generated test cases and tell me where they're wrong. Not where they're incomplete — where a real QA lead would actually disagree with the model's judgment. That feedback is worth more to this project than another feature.",
  },
  {
    role: "Applied AI / LLM Engineers",
    forWhom:
      "The retrieval layer is deliberately simple right now — TF-IDF cosine similarity, no embeddings, no vector store — and the reasoning for that restraint is written into the code, not just the docs.",
    ask: "Tell me if that restraint is still correct, or if it's time to earn the added complexity of an embedding-based retrieval layer. And if the structured-output validation around every LLM call has a hole in it I haven't found, I want to know before a real user does.",
  },
  {
    role: "Backend & Platform Engineers",
    forWhom:
      "Three of ten modules are real and wired. The other seven have a real interface contract waiting for them, a Neo4j client that's never touched a live database, and zero authentication.",
    ask: "Module 4 (Execution) is first on the roadmap. It exists in the repository today, broken, and left visibly broken on purpose — hardcoded fake results, an unresolved bug — rather than hidden or deleted. If you want to build a real Playwright/Temporal execution loop against a real interface contract, that's the single highest-leverage contribution available right now.",
  },
  {
    role: "Engineering Leaders piloting QA workflows",
    forWhom:
      "Everything above is informed guessing about what a real QA organization needs. It hasn't run against a real backlog, a real team, or a real on-call rotation yet.",
    ask: "If you'd be willing to pilot the working slice — risk-score and generate tests for a real sprint's worth of requirements — against your own review process, the gap between what I've assumed and what you'd actually need is exactly what I want to find.",
  },
];

/**
 * "Where I need help" — an explicit, honest collaboration call. Kononenko
 * conventions applied: hairline-divided rows (the office-locations list
 * pattern), a hard-cut hover state, monochrome throughout.
 */
export function Collaborate() {
  return (
    <div>
      <div className="grid gap-px overflow-hidden border border-line bg-line sm:grid-cols-2">
        {personas.map((p) => (
          <div key={p.role} className="row-hover group bg-bg p-6 md:p-7">
            <p className="font-mono-label text-[10px] text-ink-muted group-hover:text-white/60">
              For
            </p>
            <p className="font-display mt-2 text-[20px] leading-[1.2] text-ink md:text-[22px] group-hover:text-white">
              {p.role}
            </p>
            <p className="mt-4 font-sans text-[13.5px] leading-relaxed text-ink-muted group-hover:text-white/80">
              {p.forWhom}
            </p>
            <p className="mt-4 font-caption text-[15px] leading-relaxed text-ink group-hover:text-white">
              &ldquo;{p.ask}&rdquo;
            </p>
          </div>
        ))}
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-line pt-6">
        <a
          href={`mailto:${site.contactEmail}`}
          className="border-b-[1.5px] border-ink pb-[2px] font-sans text-[14px] text-ink"
        >
          {site.contactEmail} ↗
        </a>
        <a
          href={site.githubUrl}
          className="border-b-[1.5px] border-transparent pb-[2px] font-sans text-[14px] text-ink-muted hover:border-ink hover:text-ink"
        >
          Open an issue on GitHub ↗
        </a>
        <span className="font-mono-label text-[10px] text-ink-faint">
          no pitch deck, no call required — a direct message is enough
        </span>
      </div>
    </div>
  );
}
