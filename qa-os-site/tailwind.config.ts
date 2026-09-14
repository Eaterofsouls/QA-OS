import type { Config } from "tailwindcss";

// ---------------------------------------------------------------------------
// Color system — rebuilt to the Kononenko design DNA (see kononenko_handoff
// audit: MISSION_CONTROL.md / DESKTOP_AUDIT_DRAFT.md §15.5, §17).
//
// Hard rule, carried over verbatim: interface color is forbidden. Every
// token below has zero saturation — pure white, pure black, or a step on a
// neutral gray ramp. The four "status" tokens used to be hued (olive/navy/
// brick/grey); they're now a confidence ramp from black (verified, real) to
// light gray (aspirational, not built) — the same four-way distinction the
// site needs, carried entirely by value, never by hue.
// ---------------------------------------------------------------------------
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "#FFFFFF",
        "bg-elevated": "#FFFFFF",
        "bg-black": "#000000",
        ink: "#000000",
        "ink-muted": "#6B6B6B",
        "ink-faint": "#9A9A9A",
        line: "#D8D8D8",
        "line-strong": "#000000",
        status: {
          implemented: "#000000",
          partial: "#4A4A4A",
          planned: "#8A8A8A",
          vision: "#B7B7B7",
        },
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "ui-serif", "serif"],
        caption: ["Georgia", "Times New Roman", "ui-serif", "serif"],
        sans: [
          "General Sans",
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        mono: [
          "IBM Plex Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
      maxWidth: {
        prose: "760px",
        "prose-narrow": "680px",
      },
      borderRadius: {
        none: "0px",
        sm: "0px",
        DEFAULT: "0px",
        md: "0px",
        lg: "0px",
        xl: "0px",
        "2xl": "0px",
        full: "0px",
      },
      transitionTimingFunction: {
        "editorial-out": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      keyframes: {
        "draw-line": {
          "0%": { transform: "scaleX(0)" },
          "100%": { transform: "scaleX(1)" },
        },
      },
      animation: {
        "draw-line": "draw-line 700ms cubic-bezier(0.16, 1, 0.3, 1) forwards",
      },
    },
  },
  plugins: [],
};

export default config;
