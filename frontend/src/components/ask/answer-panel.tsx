"use client";

import { Check, CheckCircle2, CircleAlert, Copy } from "lucide-react";
import { useState } from "react";
import { ProvenanceRail } from "@/components/policygpt/provenance-rail";
import { Button } from "@/components/ui/button";
import type { AskResult } from "@/lib/domain/ask";
import { ConfidenceSummary } from "./confidence-summary";
import { ResultEngineeringDetails } from "./result-engineering-details";

export function AnswerPanel({
  result,
  variant,
  focusRef,
}: {
  result: AskResult;
  variant: "supported" | "provider_fallback";
  focusRef?: React.Ref<HTMLElement>;
}) {
  const [copied, setCopied] = useState(false);
  const isFallback = variant === "provider_fallback";
  const StatusIcon = isFallback ? CircleAlert : CheckCircle2;
  const pages = [...new Set(result.citations.map((citation) => citation.page))];
  const provenanceSummary = `${result.citations.length} ${
    result.citations.length === 1 ? "source" : "sources"
  } · pages ${pages.join(", ")} · ${result.citations[0]?.support ?? "Evidence"} evidence`;

  async function copyAnswer() {
    if (!result.answer) return;
    await navigator.clipboard.writeText(result.answer);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <section
      ref={focusRef}
      tabIndex={-1}
      aria-labelledby="answer-result-heading"
      className="rounded-xl border border-neutral-200 bg-white p-5 outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
    >
      <div
        role="status"
        className={
          isFallback
            ? "flex gap-3 rounded-lg border border-warning-200 bg-warning-50 p-3.5 text-warning-700"
            : "flex gap-3 rounded-lg border border-success-200 bg-success-50 p-3.5 text-success-700"
        }
      >
        <StatusIcon aria-hidden="true" className="mt-0.5 shrink-0" size={18} strokeWidth={1.75} />
        <div className="min-w-0">
          <h2 id="answer-result-heading" className="text-sm font-semibold">
            {isFallback
              ? "Answer service unavailable — evidence still available"
              : "Evidence-backed answer"}
          </h2>
          <p className="mt-1 text-sm leading-5 opacity-90">
            {isFallback
              ? "Relevant policy evidence passed the evidence gate. Review the cited passages directly."
              : "The answer is grounded in the cited policy excerpts."}
          </p>
          {isFallback && (result.provider || result.model) ? (
            <p className="font-metric mt-2 break-words text-[11px] opacity-85">
              {[result.provider, result.model].filter(Boolean).join(" · ")}
            </p>
          ) : null}
        </div>
      </div>

      {!isFallback && result.answer ? (
        <div className="mt-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-base font-semibold text-neutral-900">Answer</h3>
            <Button type="button" variant="outline" size="sm" onClick={copyAnswer}>
              {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
              {copied ? "Copied" : "Copy answer"}
            </Button>
          </div>
          <p className="mt-3 whitespace-pre-wrap text-[15px] leading-7 text-neutral-800">
            {result.answer}
          </p>
          <div className="sr-only" aria-live="polite">
            {copied ? "Answer copied." : ""}
          </div>
        </div>
      ) : null}

      <div className="mt-4">
        <ProvenanceRail summary={provenanceSummary} />
      </div>

      <div className="mt-4">
        <ConfidenceSummary confidence={result.confidence} />
      </div>

      <div className="mt-4">
        <ResultEngineeringDetails result={result} />
      </div>

      <p className="mt-4 border-t border-neutral-100 pt-4 text-xs leading-5 text-neutral-600">
        {isFallback
          ? "Generated-answer service was unavailable. Review the cited source evidence before making a formal HR, legal, or compliance decision."
          : "This response is grounded in indexed policy documents. Review the cited source evidence before making a formal HR, legal, or compliance decision."}
      </p>
    </section>
  );
}
