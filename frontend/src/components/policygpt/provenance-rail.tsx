import { FileText, LocateFixed } from "lucide-react";
import { cn } from "@/lib/utils";

export function ProvenanceRail({
  document,
  page,
  section,
  support,
  mode = "compact",
  retrievalScore,
  confidence,
}: {
  document: string;
  page: string | number;
  section: string;
  support: string;
  mode?: "compact" | "detailed";
  retrievalScore?: number;
  confidence?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-neutral-200 bg-white",
        mode === "detailed" && "p-4",
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
        <div className="min-w-0 text-xs font-semibold tracking-[0.025em] text-neutral-700 uppercase">
          <span>{document}</span>
          <span aria-hidden="true" className="mx-1.5 text-neutral-300">·</span>
          <span className="font-metric">p.{page}</span>
          <span aria-hidden="true" className="mx-1.5 text-neutral-300">·</span>
          <span>{section}</span>
          <span aria-hidden="true" className="mx-1.5 text-neutral-300">·</span>
          <span className="text-teal-700">{support}</span>
        </div>
      </div>
      {mode === "detailed" && (retrievalScore !== undefined || confidence) ? (
        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-neutral-100 pt-3 text-xs text-neutral-500">
          <LocateFixed aria-hidden="true" size={16} strokeWidth={1.75} />
          {retrievalScore !== undefined ? (
            <span className="font-metric">retrieval {retrievalScore.toFixed(4)}</span>
          ) : null}
          {confidence ? <span>Evidence confidence: {confidence}</span> : null}
        </div>
      ) : null}
    </div>
  );
}
