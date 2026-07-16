import { Check, Circle, CircleAlert, LoaderCircle } from "lucide-react";
import { lifecyclePresentation, safeErrorCodeLabels } from "@/lib/domain/document";
import type { DocumentDetail } from "@/lib/domain/document";
import { cn } from "@/lib/utils";

export function DocumentLifecycle({ document }: { document: DocumentDetail }) {
  const steps = lifecyclePresentation(document);
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-5" aria-labelledby="lifecycle-title">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="lifecycle-title" className="text-base font-semibold text-neutral-900">Ingestion lifecycle</h2>
          <p className="mt-1 text-sm leading-6 text-neutral-600">Truthful processing stages recorded by the metadata service.</p>
        </div>
        {document.status === "failed" ? (
          <span className="text-sm font-medium text-error-700">
            {document.error_code ? safeErrorCodeLabels[document.error_code] ?? "Processing failed" : "Processing failed"}
          </span>
        ) : null}
      </div>
      <ol className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {steps.map((step) => {
          const Icon = step.state === "complete" ? Check : step.state === "active" ? LoaderCircle : step.state === "failed" ? CircleAlert : Circle;
          return (
            <li key={step.stage} className={cn(
              "flex min-w-0 items-center gap-2.5 rounded-lg border px-3 py-3 text-sm",
              step.state === "complete" && "border-success-200 bg-success-50 text-success-700",
              step.state === "active" && "border-info-200 bg-info-50 font-medium text-info-700",
              step.state === "failed" && "border-error-200 bg-error-50 font-medium text-error-700",
              step.state === "pending" && "border-neutral-200 bg-neutral-50 text-neutral-500",
            )}>
              <Icon aria-hidden="true" className={cn("shrink-0", step.state === "active" && "animate-spin")} size={17} />
              <span className="min-w-0 break-words">{step.label}</span>
              <span className="sr-only">— {step.state}</span>
            </li>
          );
        })}
      </ol>
      {document.status === "failed" && document.error_message ? (
        <p className="mt-4 rounded-lg border border-error-200 bg-error-50 p-3 text-sm leading-6 text-error-700">{document.error_message}</p>
      ) : null}
    </section>
  );
}
