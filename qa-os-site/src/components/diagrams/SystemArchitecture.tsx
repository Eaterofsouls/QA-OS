"use client";

import { useState } from "react";
import { StatusLegend } from "./StatusLegend";

interface Tier {
  label: string;
  sublabel: string;
  boxes: { name: string; status: "IMPLEMENTED" | "PARTIAL" | "PLANNED"; note?: string }[];
}

const tiers: Tier[] = [
  {
    label: "apps/web",
    sublabel: "Next.js 14 + Tailwind — the Command Center UI",
    boxes: [{ name: "Command Center", status: "IMPLEMENTED" }],
  },
  {
    label: "services/api",
    sublabel: "FastAPI — six real, DI'd, honestly-erroring routes",
    boxes: [{ name: "main.py", status: "IMPLEMENTED" }],
  },
  {
    label: "packages",
    sublabel: "shared libraries",
    boxes: [
      { name: "kg-client", status: "IMPLEMENTED" },
      { name: "llm-gateway-client", status: "IMPLEMENTED" },
      { name: "extraction", status: "IMPLEMENTED" },
      { name: "connector-contract", status: "IMPLEMENTED" },
      { name: "schemas", status: "PLANNED", note: "empty — entity classes, no fields yet" },
      { name: "config-service", status: "PLANNED", note: "empty" },
      { name: "rendering", status: "PLANNED", note: "empty" },
      { name: "evaluation", status: "PLANNED", note: "empty" },
    ],
  },
  {
    label: "modules/01–09",
    sublabel: "the reasoning pipeline, exactly as it exists in the repo today",
    boxes: [
      { name: "01 Risk Assessor", status: "IMPLEMENTED" },
      { name: "02 Test Generator", status: "IMPLEMENTED" },
      { name: "03 Review Gate", status: "IMPLEMENTED" },
      { name: "05/06 Triage · Readiness", status: "PARTIAL" },
      { name: "04 Execution", status: "PLANNED", note: "in the repo — broken on purpose, not hidden" },
      { name: "07–09", status: "PLANNED", note: "empty scaffolding" },
    ],
  },
  {
    label: "services/connectors",
    sublabel: "Module 10 — Integration & Extensibility Layer, not yet wired to any route",
    boxes: [
      { name: "Jira adapter", status: "PARTIAL", note: "real auth + translation" },
      { name: "GitHub / Slack / Playwright", status: "PLANNED", note: "one-line stub classes" },
    ],
  },
];

const kgBackends = [
  {
    name: "KGClientStub",
    status: "IMPLEMENTED" as const,
    detail: "In-memory dict. Default. Real get_related() traversal, real per-tenant isolation. Lost on restart.",
  },
  {
    name: "KGClientSQLite",
    status: "IMPLEMENTED" as const,
    detail: "Same semantics as the stub, backed by a local SQLite file. Selected via KG_SQLITE_PATH. Survives a restart — verified across two separate OS processes.",
  },
  {
    name: "KGClient (Neo4j)",
    status: "PARTIAL" as const,
    detail: "Real driver code behind the identical interface. Selected via NEO4J_URI. Never exercised against a live Neo4j instance in this environment — built, not proven.",
  },
];

/**
 * Diagram 2 — System Architecture. Proves interface discipline: the KG
 * backend box explicitly shows three swappable implementations behind one
 * interface, with zero call-site changes required to move between them.
 */
export function SystemArchitecture() {
  const [openBackend, setOpenBackend] = useState<string | null>(null);

  return (
    <div className="w-full">
      <StatusLegend only={["IMPLEMENTED", "PARTIAL", "PLANNED"]} className="mb-8" />

      <div className="flex flex-col items-stretch">
        {tiers.map((tier, i) => (
          <div key={tier.label} className="flex flex-col items-center">
            <div className="w-full border border-line bg-bg-elevated p-4 md:p-5">
              <div className="mb-3 flex items-baseline justify-between gap-2">
                <p className="font-mono-label text-[12px] text-ink">{tier.label}</p>
                <p className="font-sans text-[12px] text-ink-muted">{tier.sublabel}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {tier.boxes.map((box) => (
                  <span
                    key={box.name}
                    className="inline-flex items-center gap-[6px] border border-line bg-bg px-2.5 py-1.5 font-sans text-[12px] text-ink"
                  >
                    <StatusDot status={box.status} />
                    {box.name}
                    {box.note && (
                      <span className="text-ink-muted">({box.note})</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
            {i < tiers.length - 1 && <Connector />}
          </div>
        ))}

        <Connector />

        {/* KG backend — one interface, three implementations */}
        <div className="w-full border border-line bg-bg-elevated p-4 md:p-5">
          <div className="mb-3 flex items-baseline justify-between gap-2">
            <p className="font-mono-label text-[12px] text-ink">KGClientInterface</p>
            <p className="font-sans text-[12px] text-ink-muted">
              one interface, three swappable implementations
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {kgBackends.map((b) => {
              const isOpen = openBackend === b.name;
              return (
                <button
                  key={b.name}
                  onClick={() => setOpenBackend(isOpen ? null : b.name)}
                  className="flex flex-col items-start gap-2 border bg-bg px-3 py-3 text-left"
                  style={{
                    borderColor: isOpen ? "#000000" : "#D8D8D8",
                    borderWidth: isOpen ? "1.5px" : "1px",
                  }}
                  aria-expanded={isOpen}
                >
                  <span className="flex items-center gap-[6px] font-sans text-[13px] font-medium text-ink">
                    <StatusDot status={b.status} />
                    {b.name}
                  </span>
                  <span className="font-sans text-[12px] leading-relaxed text-ink-muted">
                    {isOpen ? b.detail : "Tap for detail →"}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: "IMPLEMENTED" | "PARTIAL" | "PLANNED" }) {
  const hex =
    status === "IMPLEMENTED" ? "#000000" : status === "PARTIAL" ? "#4A4A4A" : "#8A8A8A";
  return (
    <span
      className="inline-block h-[6px] w-[6px]"
      style={{ backgroundColor: hex }}
      aria-hidden="true"
    />
  );
}

function Connector() {
  return (
    <div className="flex h-8 flex-col items-center justify-center" aria-hidden="true">
      <div className="h-full w-px bg-line" />
    </div>
  );
}
