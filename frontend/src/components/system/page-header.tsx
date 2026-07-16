import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  description,
  eyebrow,
  actions,
  className,
}: {
  title: string;
  description: string;
  eyebrow?: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-6 flex max-w-5xl items-start justify-between gap-4", className)}>
      <div className="max-w-3xl">
        {eyebrow ? (
          <div className="mb-2 text-xs font-semibold tracking-[0.12em] text-teal-700 uppercase">
            {eyebrow}
          </div>
        ) : null}
        <h1 className="text-2xl font-semibold tracking-[-0.025em] text-neutral-900 sm:text-[28px]">
          {title}
        </h1>
        <p className="mt-2 text-sm leading-6 text-neutral-600 sm:text-[15px]">
          {description}
        </p>
      </div>
      {actions ? <div className="shrink-0">{actions}</div> : null}
    </div>
  );
}
