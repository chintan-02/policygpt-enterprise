import { CircleDashed, type LucideIcon } from "lucide-react";

export function EmptyState({
  title,
  description,
  icon: Icon = CircleDashed,
  children,
}: {
  title: string;
  description: string;
  icon?: LucideIcon;
  children?: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white px-5 py-9 text-center shadow-xs sm:flex sm:min-h-[232px] sm:flex-col sm:justify-center sm:px-8 sm:py-10">
      <div className="mx-auto flex size-10 items-center justify-center rounded-lg border border-teal-100 bg-teal-50 text-teal-700">
        <Icon aria-hidden="true" size={20} strokeWidth={1.75} />
      </div>
      <h2 className="mt-4 text-base font-semibold text-neutral-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-neutral-600">
        {description}
      </p>
      {children ? <div className="mt-6">{children}</div> : null}
    </section>
  );
}
