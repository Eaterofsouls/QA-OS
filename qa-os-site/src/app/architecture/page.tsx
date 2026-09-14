import { ScrollReveal } from "@/components/ScrollReveal";
import { LifecycleMap } from "@/components/diagrams/LifecycleMap";
import { SystemArchitecture } from "@/components/diagrams/SystemArchitecture";
import { VerticalSlice } from "@/components/diagrams/VerticalSlice";
import { MemoryLayer } from "@/components/diagrams/MemoryLayer";
import { ReasoningBoundary } from "@/components/diagrams/ReasoningBoundary";
import Link from "next/link";

export const metadata = {
  title: "Architecture — QA OS",
  description:
    "The complete technical model: the 10-module lifecycle, system architecture, the real working slice, the memory layer, and where AI reasoning ends and human judgment begins.",
};

export default function ArchitecturePage() {
  return (
    <div>
      <header className="mx-auto max-w-prose px-6 pb-4 pt-16 md:px-10 md:pt-24">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">Architecture</p>
          <h1 className="font-display mt-4 text-[36px] leading-[1.15] text-ink md:text-[48px]">
            The complete technical model.
          </h1>
          <p className="mt-5 font-sans text-[16px] leading-relaxed text-ink-muted md:text-[17px]">
            Five diagrams, in order: what the ten modules are, how the
            system is actually wired, what request flow is genuinely real
            today, how memory works now versus where it's headed, and
            exactly where deterministic code stops and a model — or a
            person — takes over.
          </p>
        </ScrollReveal>
      </header>

      {/* Diagram 1 */}
      <section className="mx-auto max-w-[1400px] px-6 py-16 md:px-10 md:py-20">
        <ScrollReveal>
          <SectionHeading
            eyebrow="Diagram 01"
            title="QA Lifecycle Capability Map"
            body="Ten modules as a sequence. Colors are pulled directly from the real module-status data — not hand-painted — so this diagram can't quietly drift out of sync with what the code actually does."
          />
        </ScrollReveal>
        <ScrollReveal delay={0.08} className="mt-10">
          <LifecycleMap variant="full" />
        </ScrollReveal>
      </section>

      {/* Diagram 2 */}
      <section className="border-t border-line bg-bg-elevated py-16 md:py-20">
        <div className="mx-auto max-w-[1400px] px-6 md:px-10">
          <ScrollReveal>
            <SectionHeading
              eyebrow="Diagram 02"
              title="System Architecture"
              body="apps/web through services/api through the shared packages through the modules, down to the knowledge-graph backend — which is where real interface discipline shows up: one interface, three swappable implementations, zero call-site changes to move between them."
            />
          </ScrollReveal>
          <ScrollReveal delay={0.08} className="mt-10">
            <SystemArchitecture />
          </ScrollReveal>
        </div>
      </section>

      {/* Diagram 3 */}
      <section className="mx-auto max-w-[1400px] px-6 py-16 md:px-10 md:py-20">
        <ScrollReveal>
          <SectionHeading
            eyebrow="Diagram 03"
            title="Real Vertical-Slice Sequence"
            body="The actual working flow, step by step — hover or tap any step for the real endpoint behind it. Proves “no hardcoded output” as an architectural property, not a claim."
          />
        </ScrollReveal>
        <ScrollReveal delay={0.08} className="mt-10">
          <VerticalSlice />
        </ScrollReveal>
      </section>

      {/* Diagram 4 */}
      <section className="border-t border-line bg-bg-elevated py-16 md:py-20">
        <div className="mx-auto max-w-[1400px] px-6 md:px-10">
          <ScrollReveal>
            <SectionHeading
              eyebrow="Diagram 04"
              title="Knowledge / Memory Layer — Today vs. Vision"
              body="Where the current retrieval approach's ceiling actually is, stated plainly next to where it's headed."
            />
          </ScrollReveal>
          <ScrollReveal delay={0.08} className="mt-10">
            <MemoryLayer />
          </ScrollReveal>
        </div>
      </section>

      {/* Diagram 5 */}
      <section className="mx-auto max-w-[1400px] px-6 py-16 md:px-10 md:py-20">
        <ScrollReveal>
          <SectionHeading
            eyebrow="Diagram 05"
            title="Reasoning Boundary"
            body="The single most-asked question this site needs to pre-empt: where does AI end and judgment begin? This is the direct answer, lane by lane, across the lifecycle — including where the (not-yet-built) execution and release stages will sit once they're real."
          />
        </ScrollReveal>
        <ScrollReveal delay={0.08} className="mt-10">
          <ReasoningBoundary />
        </ScrollReveal>
      </section>

      <section className="border-t border-line py-16 md:py-20">
        <div className="mx-auto max-w-prose px-6 md:px-10">
          <ScrollReveal>
            <p className="font-display text-[22px] leading-[1.4] text-ink md:text-[26px]">
              Want the module-by-module proof behind these diagrams?
            </p>
            <Link
              href="/implementation/"
              className="mt-5 inline-block border border-ink px-5 py-3 font-sans text-[14px] text-ink hover:bg-ink hover:text-bg"
            >
              See what's actually implemented →
            </Link>
          </ScrollReveal>
        </div>
      </section>
    </div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="max-w-prose">
      <p className="font-mono-label text-[11px] text-ink-muted">{eyebrow}</p>
      <h2 className="font-sans mt-2 text-[24px] font-semibold text-ink md:text-[28px]">
        {title}
      </h2>
      <p className="mt-3 font-sans text-[15px] leading-relaxed text-ink-muted md:text-[16px]">
        {body}
      </p>
    </div>
  );
}
