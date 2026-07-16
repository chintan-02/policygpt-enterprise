import type { LucideIcon } from "lucide-react";
import type { StatusPillStatus } from "./status-pill";
import { MetricValue } from "./metric-value";
import { StatusPill } from "./status-pill";
import { cn } from "@/lib/utils";

const statusBorders: Partial<Record<StatusPillStatus, string>> = {
  operational: "border-l-success-700",
  degraded: "border-l-warning-700",
  unavailable: "border-l-error-700",
  success: "border-l-success-700",
  warning: "border-l-warning-700",
  error: "border-l-error-700",
  info: "border-l-info-700",
};

export function QualityCard({
  tier = "secondary",
  label,
  value,
  interpretation,
  status,
  statusLabel,
  icon: Icon,
  children,
  className,
}: {
  tier?: "outcome" | "secondary" | "engineering";
  label?: string;
  value?: string;
  interpretation?: string;
  status?: StatusPillStatus;
  statusLabel?: string;
  icon?: LucideIcon;
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "min-w-0 bg-white",
        tier === "outcome" &&
          "rounded-xl border border-l-[3px] border-neutral-200 border-l-neutral-300 p-5",
        tier === "secondary" &&
          "rounded-xl border border-neutral-200 p-5 shadow-xs",
        tier === "engineering" &&
          "rounded-lg border border-neutral-200 bg-transparent p-4",
        status && tier === "outcome" && statusBorders[status],
        className,
      )}
    >
      {label ? (
        <div className="flex items-start justify-between gap-3">
          <div className="text-sm font-medium text-neutral-600">{label}</div>
          {Icon ? (
            <Icon
              aria-hidden="true"
              className="shrink-0 text-neutral-400"
              size={18}
              strokeWidth={1.75}
            />
          ) : null}
        </div>
      ) : null}
      {value ? <MetricValue value={value} className="mt-4" /> : null}
      {status ? (
        <StatusPill status={status} label={statusLabel} className="mt-3" />
      ) : null}
      {interpretation ? (
        <p className="mt-3 text-sm leading-5 text-neutral-600">
          {interpretation}
        </p>
      ) : null}
      {children}
    </section>
  );
}
