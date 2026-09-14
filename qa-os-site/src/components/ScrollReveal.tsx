"use client";

import { motion, useReducedMotion as useFramerReducedMotion } from "framer-motion";
import { ReactNode } from "react";

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /** Vertical travel distance in px before settling. 12–20px per spec §6. */
  distance?: number;
  as?: "div" | "section" | "li";
}

/**
 * Base motion mechanic for the site (master spec §6): sections fade + slide
 * in as they cross a viewport threshold, 400–600ms, ease-out. Respects
 * prefers-reduced-motion automatically via Framer Motion's own hook —
 * content still appears, just without the transform/opacity animation.
 */
export function ScrollReveal({
  children,
  className,
  delay = 0,
  distance = 16,
  as = "div",
}: ScrollRevealProps) {
  const prefersReduced = useFramerReducedMotion();
  const Component = motion[as];

  if (prefersReduced) {
    const Static = as;
    return <Static className={className}>{children}</Static>;
  }

  return (
    <Component
      className={className}
      initial={{ opacity: 0, y: distance }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.18 }}
      transition={{ duration: 0.55, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </Component>
  );
}
