import { CheckCircle2, CircleAlert, CircleDot, CircleX } from "lucide-react";
import type { HealthStatus } from "@/lib/api/types";
import { titleCase } from "@/lib/formatters";
import { cn } from "@/lib/utils";

export type StatusPillStatus =
  | HealthStatus
  | "success"
  | "warning"
  | "error"
  | "info"
  | "neutral";

const styles: Record<StatusPillStatus, string> = {
  operational: "border-success-200 bg-success-50 text-success-700",
  degraded: "border-warning-200 bg-warning-50 text-warning-700",
  unavailable: "border-error-200 bg-error-50 text-error-700",
  success: "border-success-200 bg-success-50 text-success-700",
  warning: "border-warning-200 bg-warning-50 text-warning-700",
  error: "border-error-200 bg-error-50 text-error-700",
  info: "border-info-200 bg-info-50 text-info-700",
  neutral: "border-neutral-200 bg-neutral-50 text-neutral-600",
};

const icons: Record<StatusPillStatus, typeof CircleDot> = {
  operational: CheckCircle2,
  degraded: CircleAlert,
  unavailable: CircleX,
  success: CheckCircle2,
  warning: CircleAlert,
  error: CircleX,
  info: CircleDot,
  neutral: CircleDot,
};

export function StatusPill({
  status,
  label,
  compact = false,
  inverse = false,
  className,
}: {
  status: StatusPillStatus;
  label?: string;
  compact?: boolean;
  inverse?: boolean;
  className?: string;
}) {
  const Icon = icons[status];

  return (
    <span
      className={cn(
        "inline-flex w-fit items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold whitespace-nowrap",
        styles[status],
        compact && "px-2 py-0.5 text-[10px]",
        inverse && "border-white/15 bg-white/8 text-white",
        className,
      )}
    >
      <Icon aria-hidden="true" size={compact ? 16 : 16} strokeWidth={1.75} />
      {label ?? titleCase(status)}
    </span>
  );
}
