import { ChevronDown, Wrench } from "lucide-react";

export function EngineeringPanel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <details className="group rounded-lg border border-neutral-200 bg-transparent text-sm">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 font-medium text-neutral-700 marker:hidden">
        <Wrench aria-hidden="true" size={16} strokeWidth={1.75} />
        <span>{title}</span>
        <ChevronDown
          aria-hidden="true"
          className="ml-auto transition-transform group-open:rotate-180"
          size={16}
          strokeWidth={1.75}
        />
      </summary>
      <div className="border-t border-neutral-200 px-4 py-3 text-neutral-500">
        {children}
      </div>
    </details>
  );
}
