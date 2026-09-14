"use client";

import { useEffect, useState } from "react";

/**
 * Mirrors the user's prefers-reduced-motion setting.
 * Every scroll-reveal and the pinned intro sequence read this to decide
 * between an animated version and a fully static fallback, per the
 * master build spec §6: "every scroll-reveal and the intro sequence must
 * have a complete non-animated fallback."
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(query.matches);
    const listener = (event: MediaQueryListEvent) => setReduced(event.matches);
    query.addEventListener("change", listener);
    return () => query.removeEventListener("change", listener);
  }, []);

  return reduced;
}
