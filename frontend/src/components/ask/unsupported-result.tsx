import { ShieldCheck } from "lucide-react";
import type { AskResult } from "@/lib/domain/ask";
import { ResultEngineeringDetails } from "./result-engineering-details";

export function UnsupportedResult({
  result,
  focusRef,
}: {
  result: AskResult;
  focusRef?: React.Ref<HTMLElement>;
}) {
  const reason =
    result.confidence.reasons[0] ??
    "The retrieved evidence did not meet the configured support threshold.";

  return (
    <section
      ref={focusRef}
      tabIndex={-1}
      aria-labelledby="unsupported-heading"
      className="rounded-xl border border-neutral-200 border-l-[3px] border-l-info-700 bg-white p-5 outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
    >
      <div className="flex gap-3" role="status">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-info-200 bg-info-50 text-info-700">
          <ShieldCheck aria-hidden="true" size={18} strokeWidth={1.75} />
        </div>
        <div className="min-w-0">
          <h2 id="unsupported-heading" className="text-base font-semibold text-neutral-900">
            Not supported by indexed policies
          </h2>
          <p className="mt-1 text-sm leading-6 text-neutral-600">
            PolicyGPT could not find sufficient indexed document evidence to answer this question reliably.
          </p>
        </div>
      </div>

      <dl className="mt-4 grid gap-3 rounded-lg border border-neutral-200 bg-neutral-50 p-4 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs font-semibold tracking-[0.07em] text-neutral-500 uppercase">
            Evidence status
          </dt>
          <dd className="mt-1 font-semibold text-neutral-800">Insufficient</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold tracking-[0.07em] text-neutral-500 uppercase">
            Search scope
          </dt>
          <dd className="mt-1 font-semibold text-neutral-800">All indexed documents</dd>
        </div>
      </dl>

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-neutral-800">Decision reason</h3>
        <p className="mt-1 text-sm leading-6 text-neutral-600">{reason}</p>
      </div>

      <p className="mt-4 border-t border-neutral-100 pt-4 text-sm leading-6 text-neutral-600">
        Rephrase the question, or try again after the relevant policy has been indexed.
      </p>

      <div className="mt-4">
        <ResultEngineeringDetails result={result} />
      </div>
    </section>
  );
}
