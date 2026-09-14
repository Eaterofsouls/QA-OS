import Link from "next/link";
import { ScrollReveal } from "@/components/ScrollReveal";
import { StatusTag } from "@/components/StatusTag";
import { StatusLegend } from "@/components/diagrams/StatusLegend";
import { modules, moduleCountSummary } from "@/lib/modules";

export const metadata = {
  title: "Implementation — QA OS",
  description:
    "Module-by-module status, engineering decisions and why, and current limitations stated plainly. 3 of 10 planned modules are real and wired today.",
};

const engineeringDecisions = [
  {
    title: "Error-honesty over silent fallbacks",
    body: "Every LLM call that fails raises a real error, all the way up the stack. No route silently returns an empty success or a fabricated default when the model call breaks — which is a specific, common failure mode in vibe-coded AI scaffolds that this codebase's own engineering history found and fixed.",
  },
  {
    title: "Retrieval before fine-tuning",
    body: "Module 1's memory loop is retrieval-augmented prompting — real stored requirements and real human decisions injected as context — not model fine-tuning. No model weights change anywhere in this system. That's a deliberate sequencing choice, not a limitation; see /roadmap for why it's the correct first step.",
  },
  {
    title: "Interface-first persistence",
    body: "The knowledge-graph client is defined as an interface with three implementations — an in-memory stub, a SQLite-backed store, and a Neo4j production client — selected entirely through environment configuration. No call site anywhere in the codebase knows or cares which one is active.",
  },
  {
    title: "The human checkpoint is structural, not incidental",
    body: "Module 3's review gate isn't a UI nicety bolted on afterward — it's the point in the pipeline where a generated test becomes real, and the decision it produces is what feeds Module 1's memory loop. The architecture makes the human sign-off load-bearing.",
  },
];

const limitations = [
  "Module 4 (Execution Orchestrator) is in the repository and it's broken — left that way on purpose rather than deleted or hidden. It hardcodes a passing result for every test and has an unresolved bug (a missing import). Nothing downstream of execution should be trusted until it's rebuilt for real, which is exactly why it's first on the roadmap.",
  "There is no authentication. The auth check is a one-line placeholder; nothing is enforced.",
  "Retrieval memory covers Module 1's prompt only. Test generation and defect triage don't use retrieval yet.",
  "The Neo4j-backed KG client has real driver code behind the correct interface, but has never been exercised against a live Neo4j instance in this environment — built, not proven.",
  "There is currently no automated way to check whether a change to a reasoning prompt made output better or worse — only that it changed. Evaluation is unbuilt, not just unwired.",
  "The Jira connector is genuinely production-quality but isn't wired into the running flow yet. The GitHub, Slack, and Playwright connectors are also in the repository, and they're exactly what they look like: one-line stub classes with no real logic behind them yet.",
];

export default function ImplementationPage() {
  return (
    <div>
      <header className="mx-auto max-w-prose px-6 pb-4 pt-16 md:px-10 md:pt-24">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">Implementation</p>
          <h1 className="font-display mt-4 text-[36px] leading-[1.15] text-ink md:text-[48px]">
            {moduleCountSummary.implemented} of {moduleCountSummary.total}{" "}
            planned modules are real and wired today.
          </h1>
          <p className="mt-5 font-sans text-[16px] leading-relaxed text-ink-muted md:text-[17px]">
            Here's exactly which, and exactly what's next. Nothing below is
            rounded up.
          </p>
        </ScrollReveal>
      </header>

      {/* Module table */}
      <section className="mx-auto max-w-[1400px] px-6 py-14 md:px-10 md:py-16">
        <ScrollReveal>
          <StatusLegend />
        </ScrollReveal>

        <div className="mt-8 flex flex-col gap-3">
          {modules.map((m, i) => (
            <ScrollReveal key={m.id} delay={Math.min(i * 0.03, 0.2)}>
              <div className="flex flex-col gap-3 border border-line bg-bg-elevated p-5 md:flex-row md:items-start md:justify-between md:gap-6 md:p-6">
                <div className="md:w-1/3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono-label text-[11px] text-ink-muted">
                      {String(m.id).padStart(2, "0")}
                    </span>
                    <p className="font-sans text-[16px] font-medium text-ink">
                      {m.name}
                    </p>
                  </div>
                  <p className="mt-2 font-sans text-[13px] text-ink-muted">
                    {m.purpose}
                  </p>
                </div>
                <div className="md:w-2/3">
                  <div className="flex items-center justify-between gap-3 md:justify-end">
                    <StatusTag status={m.status} />
                    <span className="font-mono-label text-[11px] text-ink-muted md:hidden">
                      {m.route}
                    </span>
                  </div>
                  <p className="mt-2 font-sans text-[14px] leading-relaxed text-ink-muted">
                    {m.detail}
                  </p>
                  <p className="mt-2 hidden font-mono-label text-[11px] text-ink-muted md:block">
                    {m.route}
                  </p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </section>

      {/* Engineering decisions */}
      <section className="border-t border-line bg-bg-elevated py-16 md:py-20">
        <div className="mx-auto max-w-[1400px] px-6 md:px-10">
          <ScrollReveal>
            <p className="font-mono-label text-[11px] text-ink-muted">
              Engineering decisions
            </p>
            <h2 className="font-sans mt-2 text-[24px] font-semibold text-ink md:text-[28px]">
              Why it's built this way
            </h2>
          </ScrollReveal>

          <div className="mt-10 grid gap-8 sm:grid-cols-2">
            {engineeringDecisions.map((d, i) => (
              <ScrollReveal key={d.title} delay={Math.min(i * 0.05, 0.2)}>
                <p className="font-sans text-[15px] font-medium text-ink">
                  {d.title}
                </p>
                <p className="mt-2 font-sans text-[14px] leading-relaxed text-ink-muted">
                  {d.body}
                </p>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Limitations */}
      <section className="mx-auto max-w-prose px-6 py-16 md:px-10 md:py-20">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">
            Current limitations
          </p>
          <h2 className="font-sans mt-2 text-[24px] font-semibold text-ink md:text-[28px]">
            Stated plainly
          </h2>
        </ScrollReveal>

        <ul className="mt-8 flex flex-col gap-5">
          {limitations.map((line, i) => (
            <ScrollReveal key={i} delay={Math.min(i * 0.03, 0.18)} as="li">
              <div className="flex gap-3">
                <span
                  className="mt-[7px] h-[5px] w-[5px] flex-shrink-0 bg-status-partial"
                  aria-hidden="true"
                />
                <span className="font-sans text-[15px] leading-relaxed text-ink-muted">
                  {line}
                </span>
              </div>
            </ScrollReveal>
          ))}
        </ul>
      </section>

      <section className="border-t border-line py-16 md:py-20">
        <div className="mx-auto max-w-prose px-6 md:px-10">
          <ScrollReveal>
            <p className="font-display text-[22px] leading-[1.4] text-ink md:text-[26px]">
              This is exactly the order it should get fixed in.
            </p>
            <Link
              href="/roadmap/"
              className="mt-5 inline-block border border-ink px-5 py-3 font-sans text-[14px] text-ink hover:bg-ink hover:text-bg"
            >
              See the roadmap
            </Link>
          </ScrollReveal>
        </div>
      </section>
    </div>
  );
}
