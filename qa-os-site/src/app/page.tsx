import Link from "next/link";
import { IntroSequence } from "@/components/IntroSequence";
import { ScrollReveal } from "@/components/ScrollReveal";
import { RealVisionSeam } from "@/components/RealVisionSeam";
import { StatusTag } from "@/components/StatusTag";
import { LifecycleMap } from "@/components/diagrams/LifecycleMap";
import { Collaborate } from "@/components/Collaborate";
import { modules, moduleCountSummary } from "@/lib/modules";
import { heroStatement, oneLineThesis, proofPoints, howItWorks } from "@/lib/site";

export default function HomePage() {
  return (
    <div>
      <IntroSequence />

      {/* Hero landing — where the pinned sequence releases into. Sell the
          vision first, before anything about status or scope. */}
      <section className="mx-auto max-w-prose px-6 py-20 md:px-10 md:py-28">
        <ScrollReveal>
          <p className="font-display text-[30px] leading-[1.25] text-ink md:text-[38px]">
            {heroStatement}
          </p>
        </ScrollReveal>
        <ScrollReveal delay={0.08}>
          <p className="mt-6 font-sans text-[17px] leading-relaxed text-ink-muted md:text-[19px]">
            {oneLineThesis}
          </p>
        </ScrollReveal>
        <ScrollReveal delay={0.14}>
          <div className="mt-9 flex flex-wrap gap-4">
            <Link
              href="/architecture/"
              className="border border-ink bg-ink px-5 py-3 font-sans text-[14px] text-bg"
            >
              See the architecture
            </Link>
            <Link
              href="/run/"
              className="border border-ink px-5 py-3 font-sans text-[14px] text-ink hover:bg-ink hover:text-bg"
            >
              Run it yourself
            </Link>
            <Link
              href="/#collaborate"
              className="border border-line px-5 py-3 font-sans text-[14px] text-ink-muted hover:border-ink hover:text-ink"
            >
              Where I need help ↓
            </Link>
          </div>
        </ScrollReveal>
      </section>

      {/* How it works — the simple, step-by-step version. No architecture
          vocabulary required here; that's what /architecture is for. */}
      <section className="border-t border-line bg-bg-elevated py-16 md:py-20">
        <div className="mx-auto max-w-[1400px] px-6 md:px-10">
          <ScrollReveal>
            <p className="font-mono-label text-[11px] text-ink-muted">
              How it works
            </p>
            <h2 className="font-display mt-3 max-w-prose text-[26px] leading-[1.3] text-ink md:text-[34px]">
              Five steps. Three of them are real today.
            </h2>
            <p className="mt-4 max-w-prose font-sans text-[15px] leading-relaxed text-ink-muted">
              This is the whole loop, in plain language — no diagram required
              yet. If you want the deep architectural version, that's a
              separate page; this is the one anyone can read.
            </p>
            <div className="mt-5 flex items-center gap-3">
              <StatusTag status="IMPLEMENTED" />
              <span className="font-mono-label text-[10px] text-ink-muted">
                this exact sequence runs today, over real HTTP
              </span>
            </div>
          </ScrollReveal>

          <div className="mt-10 flex flex-col border-t border-line">
            {howItWorks.map((s, i) => (
              <ScrollReveal key={s.n} delay={Math.min(i * 0.04, 0.2)}>
                <div className="flex flex-col gap-2 border-b border-line py-6 md:flex-row md:items-baseline md:gap-8 md:py-7">
                  <div className="flex items-baseline gap-4 md:w-[220px] md:flex-shrink-0">
                    <span className="font-mono-label text-[13px] text-ink-muted">
                      {s.n}
                    </span>
                    <span className="font-mono-label text-[10px] text-ink-faint">
                      [{s.tag}]
                    </span>
                  </div>
                  <div className="flex-1">
                    <p className="font-sans text-[17px] font-medium text-ink md:text-[18px]">
                      {s.title}
                    </p>
                    <p className="mt-1.5 max-w-2xl font-sans text-[14.5px] leading-relaxed text-ink-muted">
                      {s.body}
                    </p>
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>

          <ScrollReveal delay={0.1}>
            <p className="font-caption mt-8 max-w-prose text-[17px] leading-relaxed text-ink">
              That's the entire real, working slice. Everything past step
              five — running the tests, triaging failures, deciding if a
              release is ready — is the vision the rest of this page is
              honest about not having built yet.
            </p>
          </ScrollReveal>
        </div>
      </section>

      {/* End-to-end scenario — the same five steps, made concrete with a
          real example, plus where the vision picks up. */}
      <section className="mx-auto max-w-prose px-6 py-16 md:px-10 md:py-20">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">
            The same loop, with a real example
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.05} className="mt-6">
          <div className="flex items-center gap-3">
            <StatusTag status="IMPLEMENTED" />
            <span className="font-mono-label text-[10px] text-ink-muted">
              this runs today
            </span>
          </div>
          <p className="mt-4 font-sans text-[16px] leading-relaxed text-ink md:text-[17px]">
            A requirement arrives:{" "}
            <em className="font-display not-italic">
              &ldquo;Users must be able to log in via OAuth2, including token
              refresh and session expiry.&rdquo;
            </em>{" "}
            QA OS checks its memory for similar past requirements — finds
            two, one flagged high-risk and approved, one rejected as
            over-tested. It scores this one's risk (0.82, high — auth
            surface, external-facing) informed by that history, and
            generates candidate test cases. A QA lead reviews them in the
            pending-review queue, approves one, rejects the other with a
            note. That decision is now in memory for the next auth-related
            requirement that comes in.
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.05}>
          <RealVisionSeam />
        </ScrollReveal>

        <ScrollReveal delay={0.05}>
          <div className="flex items-center gap-3">
            <StatusTag status="VISION" />
            <span className="font-mono-label text-[10px] text-status-vision">
              the direction, not built yet
            </span>
          </div>
          <p className="font-display mt-4 text-[17px] leading-relaxed text-ink md:text-[18px]">
            The approved tests execute. One fails. QA OS investigates: is
            this a real regression, a flaky test, an environment issue, or a
            test defect? It checks whether this code path changed recently
            and whether a similar failure happened before. It helps triage
            a defect, tags it to the requirement and the historical
            pattern, and factors it into release readiness. Months later, a
            new engineer asks "what happened the last time we touched the
            session-refresh flow?" — and QA OS has an answer, because
            the reasoning was never allowed to evaporate.
          </p>
        </ScrollReveal>
      </section>

      {/* Vision vs Today — the module ledger, framed as an engineering
          credibility section as much as a status report. */}
      <section className="border-y border-line bg-bg-elevated py-16 md:py-20">
        <div className="mx-auto max-w-[1400px] px-6 md:px-10">
          <ScrollReveal>
            <p className="font-mono-label text-[11px] text-ink-muted">
              What's real, what's next
            </p>
            <p className="font-display mt-3 max-w-prose text-[26px] leading-[1.3] text-ink md:text-[32px]">
              {moduleCountSummary.implemented} of {moduleCountSummary.total}{" "}
              planned modules are real and wired today. Here's exactly
              which — and exactly what's next.
            </p>
            <p className="mt-4 max-w-prose font-sans text-[15px] leading-relaxed text-ink-muted">
              The honesty here isn't modesty — it's the engineering
              signal. Anyone can claim a system works. Fewer people
              publish a line-by-line map of exactly which three parts do,
              and delete the parts that only pretended to. That map is
              below, and it's the same one this codebase's own README
              uses to audit itself.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={0.08} className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {modules.map((m) => (
              <div
                key={m.id}
                className="flex flex-col gap-2 border border-line bg-bg px-4 py-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-sans text-[13px] font-medium text-ink">
                    {String(m.id).padStart(2, "0")} · {m.short}
                  </span>
                  <StatusTag status={m.status} />
                </div>
                <p className="font-sans text-[12.5px] leading-relaxed text-ink-muted">
                  {m.purpose}
                </p>
              </div>
            ))}
          </ScrollReveal>

          <ScrollReveal delay={0.12}>
            <Link
              href="/implementation/"
              className="mt-8 inline-block border-b-[1.5px] border-line pb-[2px] font-sans text-[14px] text-ink hover:border-ink"
            >
              See the full module-by-module breakdown →
            </Link>
          </ScrollReveal>
        </div>
      </section>

      {/* Architecture teaser */}
      <section className="mx-auto max-w-[1400px] px-6 py-16 md:px-10 md:py-20">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">
            The lifecycle
          </p>
          <p className="font-display mt-3 max-w-prose text-[26px] leading-[1.3] text-ink md:text-[32px]">
            Ten modules, one pipeline — marked by what's actually true.
          </p>
        </ScrollReveal>
        <ScrollReveal delay={0.08} className="mt-10">
          <LifecycleMap variant="teaser" />
        </ScrollReveal>
        <ScrollReveal delay={0.1}>
          <Link
            href="/architecture/"
            className="mt-8 inline-block border-b-[1.5px] border-line pb-[2px] font-sans text-[14px] text-ink hover:border-ink"
          >
            See the full architecture →
          </Link>
        </ScrollReveal>
      </section>

      {/* Proof points */}
      <section className="border-t border-line py-16 md:py-20">
        <div className="mx-auto max-w-[1400px] px-6 md:px-10">
          <ScrollReveal>
            <p className="font-mono-label text-[11px] text-ink-muted">
              Real, specific, unglamorous facts
            </p>
          </ScrollReveal>
          <ScrollReveal delay={0.06} className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {proofPoints.map((p) => (
              <div key={p.claim} className="flex flex-col gap-3">
                <StatusTag status={p.status} />
                <p className="font-sans text-[14.5px] leading-relaxed text-ink">
                  {p.claim}
                </p>
              </div>
            ))}
          </ScrollReveal>
        </div>
      </section>

      {/* Collaborate — the explicit ask */}
      <section id="collaborate" className="border-t border-line py-16 md:py-20 scroll-mt-20">
        <div className="mx-auto max-w-[1400px] px-6 md:px-10">
          <ScrollReveal>
            <p className="font-mono-label text-[11px] text-ink-muted">
              Where I need help
            </p>
            <h2 className="font-display mt-3 max-w-prose text-[26px] leading-[1.3] text-ink md:text-[34px]">
              This is a solo, honest attempt at a hard problem — it gets
              better with the right four kinds of people.
            </h2>
            <p className="mt-4 max-w-prose font-sans text-[15px] leading-relaxed text-ink-muted">
              I built the working slice alone and wrote down, as precisely
              as I could, where it's real and where it's a guess. The
              guesses are where I actually want to be told I'm wrong.
              Below is who I think can tell me that, and what I'm
              specifically asking each of them for.
            </p>
          </ScrollReveal>

          <ScrollReveal delay={0.08} className="mt-10">
            <Collaborate />
          </ScrollReveal>
        </div>
      </section>

      {/* Roadmap teaser */}
      <section className="mx-auto max-w-prose px-6 py-16 md:px-10 md:py-24">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">What's next</p>
          <p className="font-display mt-4 text-[24px] leading-[1.4] text-ink md:text-[28px]">
            The roadmap is ordered by real dependency, not a features
            wish-list — execution has to be real before feedback loops
            mean anything, and evaluation has to exist before
            specialization is worth trusting.
          </p>
          <Link
            href="/roadmap/"
            className="mt-6 inline-block border-b-[1.5px] border-line pb-[2px] font-sans text-[14px] text-ink hover:border-ink"
          >
            See the roadmap →
          </Link>
        </ScrollReveal>
      </section>
    </div>
  );
}
