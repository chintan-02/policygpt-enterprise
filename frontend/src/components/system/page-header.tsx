import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  description,
  eyebrow,
  className,
}: {
  title: string;
  description: string;
  eyebrow?: string;
  className?: string;
}) {
  return (
    <div className={cn("mb-6 max-w-3xl", className)}>
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
  );
}
