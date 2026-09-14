"use client";

import { useState } from "react";
import { modules } from "@/lib/modules";
import { StatusTag } from "@/components/StatusTag";

// Confidence ramp, not a hue system: black = real and verified, lighter gray
// = further from built. Zero saturation throughout (Kononenko design DNA,
// DESKTOP_AUDIT_DRAFT.md §15.5 — "no accent color exists anywhere").
const statusHex: Record<string, string> = {
  IMPLEMENTED: "#000000",
  PARTIAL: "#4A4A4A",
  PLANNED: "#8A8A8A",
  VISION: "#B7B7B7",
};

interface LifecycleMapProps {
  variant?: "teaser" | "full";
}

/**
 * Diagram 1 — QA Lifecycle Capability Map. Colors are generated directly
 * from src/lib/modules.ts (master spec §7: "this diagram's colors should
 * be generated from the actual module-status table... so it can't silently
 * drift out of sync with reality").
 */
export function LifecycleMap({ variant = "full" }: LifecycleMapProps) {
  const [active, setActive] = useState<number | null>(null);

  return (
    <div className="w-full">
      <div
        className="grid gap-2 md:gap-3"
        style={{
          gridTemplateColumns: `repeat(${modules.length}, minmax(0, 1fr))`,
        }}
        role="list"
        aria-label="QA OS 10-module lifecycle, colored by real implementation status"
      >
        {modules.map((m) => {
          const isActive = active === m.id;
          return (
            <button
              key={m.id}
              role="listitem"
              onMouseEnter={() => setActive(m.id)}
              onMouseLeave={() => setActive(null)}
              onFocus={() => setActive(m.id)}
              onBlur={() => setActive(null)}
              className="group flex flex-col items-start gap-2 border bg-bg-elevated px-2.5 py-3 text-left md:px-3 md:py-4"
              style={{
                borderColor: isActive ? statusHex[m.status] : "#D8D8D8",
                borderWidth: isActive ? "1.5px" : "1px",
              }}
            >
              <span className="font-mono-label text-[10px] text-ink-muted">
                {String(m.id).padStart(2, "0")}
              </span>
              <span
                className="h-[6px] w-[6px]"
                style={{ backgroundColor: statusHex[m.status] }}
                aria-hidden="true"
              />
              <span className="font-sans text-[12px] leading-tight text-ink md:text-[13px]">
                {m.short}
              </span>
            </button>
          );
        })}
      </div>

      {variant === "full" && (
        <div className="mt-6 min-h-[64px] border-t border-line pt-4">
          {active ? (
            <ModuleDetail id={active} />
          ) : (
            <p className="font-sans text-[13px] text-ink-muted">
              Hover or focus a module to see its real status.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function ModuleDetail({ id }: { id: number }) {
  const m = modules.find((mod) => mod.id === id);
  if (!m) return null;
  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <p className="font-sans text-[14px] font-medium text-ink">
          {String(m.id).padStart(2, "0")} · {m.name}
        </p>
        <StatusTag status={m.status} />
      </div>
      <p className="mt-2 max-w-2xl font-sans text-[13px] leading-relaxed text-ink-muted">
        {m.detail}
      </p>
    </div>
  );
}
