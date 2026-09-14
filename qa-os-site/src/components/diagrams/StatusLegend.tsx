import { Status, statusLabel, statusBgVar } from "@/lib/modules";

const ALL: Status[] = ["IMPLEMENTED", "PARTIAL", "PLANNED", "VISION"];

export function StatusLegend({
  only,
  className = "",
}: {
  only?: Status[];
  className?: string;
}) {
  const list = only ?? ALL;
  return (
    <div className={`flex flex-wrap items-center gap-x-5 gap-y-2 ${className}`}>
      {list.map((s) => (
        <div key={s} className="flex items-center gap-[6px]">
          <span
            className={`h-[6px] w-[6px] ${statusBgVar[s]}`}
            aria-hidden="true"
          />
          <span className="font-mono-label text-[10px] text-ink-muted">
            {statusLabel[s]}
          </span>
        </div>
      ))}
    </div>
  );
}
