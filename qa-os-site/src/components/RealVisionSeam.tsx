"use client";

import { motion, useReducedMotion as useFramerReducedMotion } from "framer-motion";

/**
 * The seam between "what's real today" and "what QA OS is becoming."
 * Gets its own distinct treatment per master spec §6: a divider that
 * visibly draws itself as the visitor scrolls into it, with a beat of
 * pause in the reveal rhythm right here — "the page should feel like
 * it takes a breath."
 */
export function RealVisionSeam() {
  const prefersReduced = useFramerReducedMotion();

  return (
    <div className="mx-auto flex max-w-prose flex-col items-center py-4">
      <div className="flex w-full items-center gap-4">
        <span className="font-mono-label whitespace-nowrap text-[11px] text-ink-muted">
          real today
        </span>
        {prefersReduced ? (
          <span className="h-px flex-1 bg-line" />
        ) : (
          <motion.span
            className="h-px flex-1 origin-left bg-line"
            initial={{ scaleX: 0 }}
            whileInView={{ scaleX: 1 }}
            viewport={{ once: true, amount: 0.8 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          />
        )}
        <span className="font-mono-label whitespace-nowrap text-[11px] text-status-vision">
          becoming
        </span>
      </div>
    </div>
  );
}
