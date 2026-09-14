import Link from "next/link";
import { ScrollReveal } from "@/components/ScrollReveal";
import { site } from "@/lib/site";

export const metadata = {
  title: "Run it — QA OS",
  description:
    "A short, accurate install guide for the real vertical slice: risk assessment, test generation, human review, and retrieval memory.",
};

const commandBlock = `# Backend
cd services/api
uv sync
export LITELLM_BASE_URL=https://api.openai.com/v1   # or any OpenAI-compatible endpoint
export LITELLM_API_KEY=sk-...
uv run uvicorn main:app --reload

# (optional) persistent demo data across restarts
export KG_SQLITE_PATH=./qa_os.sqlite3

# Frontend
cd apps/web
npm install
npm run dev
# open localhost:3000 — type a requirement, run the pipeline, approve a
# test, then click "View Graph" to see it live in the graph explorer`;

export default function RunPage() {
  return (
    <div>
      <header className="mx-auto max-w-prose px-6 pb-4 pt-16 md:px-10 md:pt-24">
        <ScrollReveal>
          <p className="font-mono-label text-[11px] text-ink-muted">Run it</p>
          <h1 className="font-display mt-4 text-[36px] leading-[1.15] text-ink md:text-[48px]">
            Ten minutes, your own key, the real thing.
          </h1>
          <p className="mt-5 font-sans text-[16px] leading-relaxed text-ink-muted md:text-[17px]">
            This runs the real vertical slice — risk assessment, test
            generation, human review, and retrieval memory — against
            whatever LLM you point it at. Everything past that (execution,
            defect triage, release readiness) is roadmap, not yet
            runnable. See{" "}
            <Link
              href="/roadmap/"
              className="text-ink underline decoration-line underline-offset-4 hover:decoration-ink"
            >
              /roadmap
            </Link>
            .
          </p>
        </ScrollReveal>
      </header>

      <section className="mx-auto max-w-prose px-6 py-10 md:px-10 md:py-14">
        <ScrollReveal>
          <pre className="overflow-x-auto border border-line bg-bg-elevated p-5 font-mono text-[13px] leading-relaxed text-ink md:p-6">
            <code>{commandBlock}</code>
          </pre>
        </ScrollReveal>

        <ScrollReveal delay={0.06}>
          <p className="mt-8 font-sans text-[15px] leading-relaxed text-ink-muted">
            Found something worth fixing, or want to wire up Module 5 or
            6? Issues and pull requests are genuinely welcome — see the
            repo for exactly where things stand.
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.1}>
          <div className="mt-8 flex flex-wrap gap-4">
            <a
              href={site.githubUrl}
              className="border border-ink bg-ink px-5 py-3 font-sans text-[14px] text-bg hover:opacity-85"
            >
              View on GitHub
            </a>
            <Link
              href="/implementation/"
              className="border border-ink px-5 py-3 font-sans text-[14px] text-ink hover:bg-ink hover:text-bg"
            >
              See what's implemented
            </Link>
          </div>
        </ScrollReveal>
      </section>

      <section className="border-t border-line py-16 md:py-20">
        <div className="mx-auto max-w-prose px-6 md:px-10">
          <ScrollReveal>
            <p className="font-mono-label text-[11px] text-ink-muted">
              Elsewhere
            </p>
            <p className="mt-3 font-sans text-[15px] leading-relaxed text-ink-muted">
              More projects, engineering philosophy, and the rest of the
              story live at{" "}
              <a
                href={site.parentUrl}
                className="text-ink underline decoration-line underline-offset-4 hover:decoration-ink"
              >
                {site.parentDomain}
              </a>
              .
            </p>
          </ScrollReveal>
        </div>
      </section>
    </div>
  );
}
