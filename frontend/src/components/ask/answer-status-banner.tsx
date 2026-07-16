import { CheckCircle2, CircleAlert, CircleX, Info } from "lucide-react";
import { cn } from "@/lib/utils";

const variants = {
  success: {
    icon: CheckCircle2,
    className: "border-success-200 bg-success-50 text-success-700",
  },
  warning: {
    icon: CircleAlert,
    className: "border-warning-200 bg-warning-50 text-warning-700",
  },
  error: {
    icon: CircleX,
    className: "border-error-200 bg-error-50 text-error-700",
  },
  neutral: {
    icon: Info,
    className: "border-neutral-200 bg-neutral-50 text-neutral-700",
  },
};

export function AnswerStatusBanner({
  variant,
  title,
  children,
  focusRef,
}: {
  variant: keyof typeof variants;
  title: string;
  children: React.ReactNode;
  focusRef?: React.Ref<HTMLDivElement>;
}) {
  const { icon: Icon, className } = variants[variant];

  return (
    <div
      ref={focusRef}
      tabIndex={-1}
      role="status"
      className={cn("flex gap-3 rounded-lg border p-4 outline-none", className)}
    >
      <Icon aria-hidden="true" className="mt-0.5 shrink-0" size={18} strokeWidth={1.75} />
      <div>
        <h2 className="text-sm font-semibold">{title}</h2>
        <div className="mt-1 text-sm leading-5 opacity-90">{children}</div>
      </div>
    </div>
  );
}
