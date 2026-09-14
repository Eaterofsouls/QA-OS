"use client";

import { useRef } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useReducedMotion as useFramerReducedMotion,
  MotionValue,
} from "framer-motion";

const CARDS = [
  {
    label: "The problem",
    line: "QA reasoning lives in tickets, chat threads, and whoever happens to remember the last time this broke.",
  },
  {
    label: "The thesis",
    line: "AI can absorb the repetitive reasoning and preserve what the organization already learned — so judgment stays human.",
  },
  {
    label: "The promise",
    line: "Here’s exactly what’s real. And exactly what’s not. Nothing in between.",
    emphasis: true,
  },
];

/**
 * The one bounded, pinned scrollytelling moment on the site (master spec §5).
 * Scroll position — not time — drives card-to-card progression via
 * transform/opacity while the viewport is pinned. Releases to native scroll
 * once the third card resolves.
 *
 * Reduced motion: renders the same three lines stacked, statically, with
 * zero pinning and zero transform, per spec.
 */
export function IntroSequence() {
  const prefersReduced = useFramerReducedMotion();
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  if (prefersReduced) {
    return (
      <section className="mx-auto flex max-w-3xl flex-col gap-10 px-6 py-24 md:px-10 md:py-32">
        {CARDS.map((card) => (
          <div key={card.label}>
            <p className="font-mono-label text-[12px] text-ink-muted">{card.label}</p>
            <p
              className={`font-display mt-3 text-[34px] leading-[1.15] text-ink md:text-[48px] ${
                card.emphasis ? "font-medium" : "font-normal"
              }`}
            >
              {card.line}
            </p>
          </div>
        ))}
      </section>
    );
  }

  return (
    <div ref={containerRef} className="relative" style={{ height: "300vh" }}>
      <div className="sticky top-0 flex h-screen items-center overflow-hidden">
        <div className="relative mx-auto h-[55vh] w-full max-w-4xl">
          {CARDS.map((card, i) => (
            <IntroCard
              key={card.label}
              index={i}
              total={CARDS.length}
              progress={scrollYProgress}
              label={card.label}
              line={card.line}
              emphasis={card.emphasis}
            />
          ))}
        </div>
        <ScrollHint progress={scrollYProgress} />
      </div>
    </div>
  );
}

function IntroCard({
  index,
  total,
  progress,
  label,
  line,
  emphasis,
}: {
  index: number;
  total: number;
  progress: MotionValue<number>;
  label: string;
  line: string;
  emphasis?: boolean;
}) {
  const segment = 1 / total;
  const start = index * segment;
  const end = start + segment;
  // Each card fades/slides in through the first ~55% of its segment, holds,
  // then fades/slides out through the last ~35% — leaving a brief pause at
  // full opacity so the line can actually be read.
  const inEnd = start + segment * 0.35;
  const outStart = end - segment * 0.3;

  const opacity = useTransform(
    progress,
    [start, inEnd, outStart, end],
    [index === 0 ? 1 : 0, 1, 1, index === total - 1 ? 1 : 0]
  );
  const y = useTransform(
    progress,
    [start, inEnd, outStart, end],
    [index === 0 ? 0 : 24, 0, 0, index === total - 1 ? 0 : -24]
  );

  return (
    <motion.div
      style={{ opacity, y }}
      className="absolute inset-0 flex flex-col justify-center px-6 md:px-10"
    >
      <p className="font-mono-label text-[12px] text-ink-muted md:text-[13px]">
        {label}
      </p>
      <p
        className={`font-display mt-4 max-w-3xl text-[36px] leading-[1.12] text-ink md:text-[64px] lg:text-[76px] ${
          emphasis ? "font-medium" : "font-normal"
        }`}
      >
        {line}
      </p>
    </motion.div>
  );
}

function ScrollHint({ progress }: { progress: MotionValue<number> }) {
  const opacity = useTransform(progress, [0, 0.08, 0.92, 1], [1, 0, 0, 0]);
  return (
    <motion.div
      style={{ opacity }}
      className="pointer-events-none absolute bottom-10 left-1/2 -translate-x-1/2 font-mono-label text-[11px] text-ink-muted"
    >
      scroll
    </motion.div>
  );
}
