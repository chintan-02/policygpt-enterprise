import { EngineeringPanel } from "@/components/policygpt/engineering-panel";
import type { AskResult } from "@/lib/domain/ask";

function RawMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt>{label}</dt>
      <dd className="font-metric text-neutral-700">{value.toFixed(4)}</dd>
    </div>
  );
}

export function ResultEngineeringDetails({ result }: { result: AskResult }) {
  const breakdown = result.confidence.breakdown;

  if (!breakdown && !result.provider && !result.model) return null;

  return (
    <EngineeringPanel title="Engineering details">
      <dl className="space-y-2 text-xs">
        <div className="flex items-center justify-between gap-4">
          <dt>Evidence status</dt>
          <dd className="font-medium text-neutral-700">{result.confidence.status}</dd>
        </div>
        {breakdown ? (
          <>
            <RawMetric label="Answerability score" value={breakdown.answerability_score} />
            <RawMetric label="Top retrieval score" value={breakdown.top_retrieval_score} />
            <RawMetric label="Average retrieval score" value={breakdown.average_retrieval_score} />
            <RawMetric label="Retrieval margin" value={breakdown.retrieval_margin} />
            <RawMetric label="Lexical coverage" value={breakdown.lexical_coverage} />
            <RawMetric
              label="Top-chunk lexical coverage"
              value={breakdown.top_chunk_lexical_coverage}
            />
            <div className="flex items-center justify-between gap-4">
              <dt>Numeric mismatch</dt>
              <dd className="font-medium text-neutral-700">
                {breakdown.numeric_mismatch ? "Yes" : "No"}
              </dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt>Scope risk</dt>
              <dd className="font-medium text-neutral-700">
                {breakdown.scope_risk ? "Yes" : "No"}
              </dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt>Direct support</dt>
              <dd className="font-medium text-neutral-700">
                {breakdown.direct_support ? "Yes" : "No"}
              </dd>
            </div>
          </>
        ) : null}
        {result.provider ? (
          <div className="flex items-center justify-between gap-4">
            <dt>Provider</dt>
            <dd className="font-medium text-neutral-700">{result.provider}</dd>
          </div>
        ) : null}
        {result.model ? (
          <div className="flex items-center justify-between gap-4">
            <dt>Model</dt>
            <dd className="max-w-[65%] break-words text-right font-medium text-neutral-700">
              {result.model}
            </dd>
          </div>
        ) : null}
      </dl>
    </EngineeringPanel>
  );
}
