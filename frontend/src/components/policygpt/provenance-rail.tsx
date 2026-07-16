import { FileText } from "lucide-react";
import { cn } from "@/lib/utils";

export function ProvenanceRail({
  document,
  page,
  section,
  support,
  summary,
  mode = "compact",
}: {
  document?: string;
  page?: string | number;
  section?: string;
  support?: string;
  summary?: string;
  mode?: "compact" | "detailed";
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-neutral-200 bg-white",
        mode === "detailed" && "bg-neutral-50 p-3",
      )}
    >
      <div
        className={cn(
          "flex min-w-0 items-center gap-2 border-l-[3px] border-l-teal-700 px-3 py-2.5",
          mode === "detailed" && "border-l-0 p-0",
        )}
      >
        <FileText
          aria-hidden="true"
          className="shrink-0 text-teal-700"
          size={16}
          strokeWidth={1.75}
        />
        <div className="font-metric min-w-0 text-[11px] leading-5 font-semibold tracking-[0.015em] text-neutral-700">
          {summary ? (
            <span className="block break-words">{summary}</span>
          ) : (
            <span className="grid min-w-0 gap-y-0.5">
              <span className="flex min-w-0 items-baseline gap-1.5 whitespace-nowrap">
                <span className="min-w-0 truncate" title={document}>{document}</span>
                <span aria-hidden="true" className="shrink-0 text-neutral-300">·</span>
                <span className="shrink-0">p.{page}</span>
              </span>
              <span className="flex min-w-0 items-baseline gap-1.5 whitespace-nowrap">
                <span className="min-w-0 truncate" title={section}>{section}</span>
                <span aria-hidden="true" className="shrink-0 text-neutral-300">·</span>
                <span className="shrink-0 text-teal-700">{support}</span>
              </span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
