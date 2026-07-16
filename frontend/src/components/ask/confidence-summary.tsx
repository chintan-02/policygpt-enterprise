import { Gauge } from "lucide-react";
import type { AskConfidence } from "@/lib/domain/ask";

export function ConfidenceSummary({ confidence }: { confidence: AskConfidence }) {
  const calibratedPercent = Math.round(confidence.score * 100);

  return (
    <section className="border-t border-neutral-100 pt-4" aria-labelledby="confidence-heading">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Gauge aria-hidden="true" className="text-teal-700" size={17} strokeWidth={1.75} />
          <h3 id="confidence-heading" className="text-sm font-semibold text-neutral-800">
            Confidence
          </h3>
        </div>
        <span className="font-metric text-sm font-semibold text-neutral-800">
          {calibratedPercent}%
        </span>
      </div>
      <p className="mt-1 text-sm font-medium text-neutral-700">{confidence.label}</p>
      {confidence.reasons.length > 0 ? (
        <ul className="mt-2 space-y-1 text-sm leading-5 text-neutral-600">
          {confidence.reasons.slice(0, 3).map((reason) => (
            <li key={reason} className="flex gap-2">
              <span aria-hidden="true" className="text-teal-700">•</span>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
