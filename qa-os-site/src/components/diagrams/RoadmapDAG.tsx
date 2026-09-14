"use client";

import { useState } from "react";
import { roadmapNodes } from "@/lib/roadmap";
import { StatusTag } from "@/components/StatusTag";

/**
 * Diagram 6 — Roadmap Dependency Graph. A DAG, not a timeline: nodes
 * connected by dependency arrows, no dates. Clicking a node expands its
 * detail inline rather than navigating away, per master spec §7.
 */
export function RoadmapDAG() {
  const [openId, setOpenId] = useState<string | null>(roadmapNodes[0]?.id ?? null);

  return (
    <div className="w-full">
      <ol className="relative flex flex-col">
        {roadmapNodes.map((node, i) => {
          const isOpen = openId === node.id;
          const isLast = i === roadmapNodes.length - 1;
          return (
            <li key={node.id} className="relative flex gap-4 md:gap-6">
              <div className="flex flex-col items-center">
                <span
                  className="z-10 flex h-8 w-8 flex-shrink-0 items-center justify-center border-2 bg-bg font-mono-label text-[11px] duration-200"
                  style={{
                    borderColor: isOpen ? "#000000" : "#D8D8D8",
                    color: "#000000",
                  }}
                >
                  {node.index}
                </span>
                {!isLast && (
                  <span className="w-px flex-1 bg-line" aria-hidden="true" />
                )}
              </div>

              <button
                onClick={() => setOpenId(isOpen ? null : node.id)}
                aria-expanded={isOpen}
                className="mb-6 flex-1 border bg-bg-elevated px-4 py-4 text-left duration-200 md:px-5"
                style={{ borderColor: isOpen ? "#000000" : "#D8D8D8" }}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-sans text-[15px] font-medium text-ink">
                    {node.title}
                  </p>
                  <StatusTag status={node.status} />
                </div>
                <p className="mt-1.5 font-sans text-[13px] text-ink-muted">
                  {node.summary}
                </p>

                {isOpen && (
                  <p className="mt-4 max-w-2xl border-t border-line pt-4 font-sans text-[14px] leading-relaxed text-ink">
                    {node.detail}
                  </p>
                )}
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
