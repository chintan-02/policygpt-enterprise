import { cn } from "@/lib/utils";

export function MetricValue({
  value,
  unit,
  numerator,
  denominator,
  size = "md",
  className,
}: {
  value?: string | number;
  unit?: string;
  numerator?: string | number;
  denominator?: string | number;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const sizeClass = {
    sm: "text-lg",
    md: "text-2xl",
    lg: "text-[30px]",
  }[size];

  return (
    <div
      className={cn(
        "font-metric flex min-w-0 items-baseline gap-1.5 font-semibold tracking-[-0.035em] text-neutral-900",
        sizeClass,
        className,
      )}
    >
      {numerator !== undefined && denominator !== undefined ? (
        <>
          <span>{numerator}</span>
          <span className="text-[0.7em] font-medium text-neutral-400">/</span>
          <span>{denominator}</span>
        </>
      ) : (
        <span className="truncate">{value}</span>
      )}
      {unit ? (
        <span className="text-[0.48em] font-medium tracking-normal text-neutral-500">
          {unit}
        </span>
      ) : null}
    </div>
  );
}
