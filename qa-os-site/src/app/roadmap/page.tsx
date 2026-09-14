import Link from "next/link";
import { ScrollReveal } from "@/components/ScrollReveal";
import { RoadmapDAG } from "@/components/diagrams/RoadmapDAG";
import { site } from "@/lib/site";

export const metadata = {
  title: "Roadmap — QA OS",
  description:
    "A dependency-aware roadmap, not a calendar: what has to be real before the next thing means anything. Plus the training/evolution plan and an open door for technical collaboration.",
};

const trainingSteps = [
  {
    step: "1",
    title: "Retrieval + structured memory first",
    body: "What's already built — cheapest, most interpretable, easiest to debug when it's wrong, and it's already producing real signal today via the Module 1 ↔ Module 3 loop.",
  },
  {
    step: "2",
    title: "Context / prompt specialization second",
    body: "Org-specific terminology, severity conventions, and known-risky-area weighting encoded as retrieved context, not baked into weights. Still fully interpretable, still cheap to iterate.",
  },
  {
    step: "3",
    title: "Evaluation-driven iteration third",
    body: "The actual gate. Without packages/evaluation being real, there's no honest way to know if steps 1–2 made anything better — only that they changed something.",
  },
  {
    step: "4",
    title: "Fine-tuning / preference learning last, and narrow",
    body: "Only once there's real labeled trace volume — hundreds of real approve/reject/correct decisions per task type — and only for specific sub-tasks where retrieval and context genuinely plateau. Full-system fine-tuning is explicitly the wrong first move: expensive, hard to debug, and it throws away the interpretability retrieval-based memory gives for free.",
  },
];

export default function RoadmapPage() {
  return (
    <div>
      <header className="mx-auto max-w-prose px-6 pb-4 pt-16 md:px-10 md:pt-24">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">Roadmap</p>
          <h1 className="font-display mt-4 text-[36px] leading-[1.15] text-ink md:text-[48px]">
            A dependency graph, not a calendar.
          </h1>
          <p className="mt-5 font-sans text-[16px] leading-relaxed text-ink-muted md:text-[17px]">
            No dates. Every arrow below is a real dependency — feedback
            loops are structurally meaningless before execution is real,
            and specialization is premature before evaluation exists to
            measure whether "specialized" is actually better.
          </p>
        </ScrollReveal>
      </header>

      <section className="mx-auto max-w-[1000px] px-6 py-14 md:px-10 md:py-16">
        <ScrollReveal>
          <RoadmapDAG />
        </ScrollReveal>
      </section>

      {/* Training / evolution plan */}
      <section className="border-t border-line bg-bg-elevated py-16 md:py-20">
        <div className="mx-auto max-w-[1200px] px-6 md:px-10">
          <ScrollReveal>
            <p className="font-mono-label text-[11px] text-ink-muted">
              Training / evolution plan
            </p>
            <h2 className="font-sans mt-2 max-w-prose text-[24px] font-semibold text-ink md:text-[28px]">
              Where "training" actually belongs — answered directly, not
              hedged
            </h2>
          </ScrollReveal>

          <div className="mt-10 grid gap-8 md:grid-cols-2">
            {trainingSteps.map((s) => (
              <ScrollReveal key={s.step} delay={Number(s.step) * 0.04}>
                <div className="flex gap-4">
                  <span className="font-mono-label text-[13px] text-ink-muted">
                    {s.step}
                  </span>
                  <div>
                    <p className="font-sans text-[15px] font-medium text-ink">
                      {s.title}
                    </p>
                    <p className="mt-2 font-sans text-[14px] leading-relaxed text-ink-muted">
                      {s.body}
                    </p>
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>

          <ScrollReveal delay={0.15} className="mt-12 max-w-prose border-t border-line pt-8">
            <p className="font-mono-label text-[11px] text-ink-muted">
              What's missing, concretely
            </p>
            <p className="mt-3 font-sans text-[15px] leading-relaxed text-ink-muted">
              Feedback should be human-labeled not just as approve/reject
              (already captured) — but <em className="font-display not-italic">why</em>,
              in structured form: wrong risk level? Missing test type?
              Tone mismatch with team convention? That's currently
              missing, and it's a real, concrete next feature — not
              vague future work.
            </p>
          </ScrollReveal>
        </div>
      </section>

      {/* Partnership vision */}
      <section className="mx-auto max-w-prose px-6 py-16 md:px-10 md:py-24">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">
            Partnership vision
          </p>
          <p className="font-display mt-4 text-[22px] leading-[1.55] text-ink md:text-[26px]">
            The foundation here is independently built and honestly
            scoped. The next real step — organization-specific
            specialization, real historical data, real feedback at
            volume — isn't something one person builds alone in good
            faith; it needs a real QA environment's data, workflows, and
            judgment.
          </p>
          <p className="mt-5 font-sans text-[16px] leading-relaxed text-ink-muted">
            If that's an interesting problem to you or your team, I'm
            open to technical collaboration, pilot work, or figuring out
            what a deeper partnership could look like. This isn't a
            sales pitch — it's an open engineering direction with a
            clear next chapter.
          </p>
          <a
            href={`mailto:${site.contactEmail}`}
            className="mt-8 inline-block border border-ink px-5 py-3 font-sans text-[14px] text-ink hover:bg-ink hover:text-bg"
          >
            Talk to me about this direction
          </a>
        </ScrollReveal>
      </section>
    </div>
  );
}
