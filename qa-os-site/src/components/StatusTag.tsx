import {
  Status,
  statusLabel,
  statusBgVar,
  statusColorVar,
  statusBorderVar,
} from "@/lib/modules";

interface StatusTagProps {
  status: Status;
  className?: string;
}

/**
 * The one non-negotiable content device on the site: every capability claim
 * carries a visible status tag. A small square mark, not a filled chip or
 * a colored dot — the mark's value (black → gray → light gray) carries the
 * confidence signal, never a hue (Kononenko design system: zero saturation
 * on every interface element, confirmed across 5+ hover states before this
 * rule was trusted — see kononenko_handoff/DESKTOP_DNA.md §6).
 */
export function StatusTag({ status, className = "" }: StatusTagProps) {
  return (
    <span
      className={`inline-flex items-center gap-[6px] align-middle font-mono-label text-[11px] leading-none text-ink-muted ${className}`}
    >
      <span
        className={`h-[6px] w-[6px] ${statusBgVar[status]}`}
        aria-hidden="true"
      />
      <span className={statusColorVar[status]}>{statusLabel[status]}</span>
    </span>
  );
}

/**
 * Underline variant — used inline within a sentence when a mark would
 * interrupt the reading line. No hover transition: this site's one hover
 * rule is hard-cut, zero-duration, never eased.
 */
export function StatusUnderline({ status, className = "" }: StatusTagProps) {
  return (
    <span
      className={`font-mono-label text-[11px] border-b-2 pb-[1px] ${statusBorderVar[status]} ${statusColorVar[status]} ${className}`}
    >
      {statusLabel[status]}
    </span>
  );
}
