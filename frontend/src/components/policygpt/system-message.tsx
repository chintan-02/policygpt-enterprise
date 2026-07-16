import { CircleAlert, CircleCheck, CircleX, Info } from "lucide-react";
import { cn } from "@/lib/utils";

const variants = {
  info: { icon: Info, style: "border-info-200 bg-info-50 text-info-700" },
  success: {
    icon: CircleCheck,
    style: "border-success-200 bg-success-50 text-success-700",
  },
  warning: {
    icon: CircleAlert,
    style: "border-warning-200 bg-warning-50 text-warning-700",
  },
  error: { icon: CircleX, style: "border-error-200 bg-error-50 text-error-700" },
};

export function SystemMessage({
  variant,
  title,
  children,
}: {
  variant: keyof typeof variants;
  title: string;
  children: React.ReactNode;
}) {
  const { icon: Icon, style } = variants[variant];

  return (
    <div className={cn("flex gap-3 rounded-lg border p-4", style)} role="status">
      <Icon aria-hidden="true" className="mt-0.5 shrink-0" size={18} strokeWidth={1.75} />
      <div>
        <div className="text-sm font-semibold">{title}</div>
        <div className="mt-1 text-sm leading-5 opacity-90">{children}</div>
      </div>
    </div>
  );
}
