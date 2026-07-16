import { Download } from "lucide-react";
import { DiagnosticRunNotice, EvaluationErrorState } from "@/components/features/evaluations/evaluation-shared";
import { QualityCard } from "@/components/policygpt/quality-card";
import { buttonVariants } from "@/components/ui/button";
import { PageHeader } from "@/components/system/page-header";
import { loadEvaluationPageState } from "@/lib/api/evaluations";
import type { EvaluationViewModel } from "@/lib/domain/evaluation";
import { formatEvaluationDate, formatEvaluationLatency } from "@/lib/formatters/evaluation";
import { cn } from "@/lib/utils";

export default async function LatestEvaluationRunPage() {
  const state = await loadEvaluationPageState();
  return (
    <>
      <PageHeader title="Latest evaluation run" description="Trace the configuration, coverage, artifact, and download outputs for the latest read-only evaluation result." />
      {state.state === "error" ? <EvaluationErrorState state={state} /> : <RunContent data={state.data} />}
    </>
  );
}

function RunRow({ label, value }: { label: string; value: React.ReactNode }) {
  return <div className="grid gap-1 border-t border-neutral-200 py-3 first:border-0 first:pt-0 sm:grid-cols-[190px_minmax(0,1fr)]"><dt className="text-sm font-medium text-neutral-600">{label}</dt><dd className="font-metric min-w-0 break-all text-sm text-neutral-900">{value}</dd></div>;
}

function RunContent({ data }: { data: EvaluationViewModel }) {
  return (
    <div className="space-y-[22px]">
      <DiagnosticRunNotice data={data} />
      <div className="flex flex-wrap gap-3">
        <a href="/api/evaluations/latest" download="policygpt-latest-evaluation.json" className={cn(buttonVariants({ variant: "outline", size: "lg" }))} aria-label="Download latest evaluation JSON"><Download aria-hidden="true" />Download JSON</a>
        <a href="/api/evaluations/latest.csv" download="policygpt-latest-evaluation.csv" className={cn(buttonVariants({ variant: "outline", size: "lg" }))} aria-label="Download latest evaluation CSV"><Download aria-hidden="true" />Download CSV</a>
      </div>
      <QualityCard tier="secondary"><h2 className="text-base font-semibold text-neutral-900">Run metadata</h2><dl className="mt-4"><RunRow label="Run ID" value={data.run.run_id} /><RunRow label="Started" value={formatEvaluationDate(data.run.started_at_utc)} /><RunRow label="Completed" value={formatEvaluationDate(data.run.completed_at_utc)} /><RunRow label="Total duration" value={formatEvaluationLatency(data.run.duration_ms)} /><RunRow label="Dataset hash" value={data.run.dataset_sha256 ?? "N/A"} /><RunRow label="Question count" value={data.run.question_count} /><RunRow label="Benchmark coverage" value={`${data.artifact.question_count} / ${data.artifact.benchmark_question_count ?? data.artifact.question_count}`} /><RunRow label="Endpoint" value={data.run.endpoint ?? "N/A"} /><RunRow label="Top-k" value={data.run.top_k ?? "N/A"} /><RunRow label="Timeout" value={data.run.timeout_seconds === null || data.run.timeout_seconds === undefined ? "N/A" : `${data.run.timeout_seconds} s`} /><RunRow label="Request delay" value={data.run.request_delay_seconds === null || data.run.request_delay_seconds === undefined ? "N/A" : `${data.run.request_delay_seconds} s`} /><RunRow label="Backend" value={data.run.backend_base_label} /><RunRow label="Artifact updated" value={formatEvaluationDate(data.artifact.updated_at)} /></dl></QualityCard>
      <QualityCard tier="secondary"><h2 className="text-base font-semibold text-neutral-900">Regenerate the artifact</h2><p className="mt-2 text-sm text-neutral-600">Run evaluations from the repository root. The browser never starts benchmark execution.</p><pre className="mt-4 overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-50 p-4 font-mono text-xs text-neutral-800"><code>python eval/run_eval.py --request-delay-seconds 5</code></pre><p className="mt-4 text-sm leading-6 text-neutral-600">Generated evaluation artifacts are ignored by Git and should be regenerated for each environment.</p></QualityCard>
    </div>
  );
}
