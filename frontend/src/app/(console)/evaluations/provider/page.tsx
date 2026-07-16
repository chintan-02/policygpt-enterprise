import { DiagnosticRunNotice, EvaluationErrorState } from "@/components/features/evaluations/evaluation-shared";
import { QualityCard } from "@/components/policygpt/quality-card";
import { SystemMessage } from "@/components/policygpt/system-message";
import { PageHeader } from "@/components/system/page-header";
import { loadEvaluationPageState } from "@/lib/api/evaluations";
import { prepareProviderStatistics, type EvaluationViewModel } from "@/lib/domain/evaluation";
import { businessLabel, formatEvaluationPercent } from "@/lib/formatters/evaluation";

export default async function EvaluationProviderPage() {
  const state = await loadEvaluationPageState();
  return (
    <>
      <PageHeader title="Provider reliability" description="Separate answer-provider generation availability from evidence retrieval and unsupported-answer safety." />
      {state.state === "error" ? <EvaluationErrorState state={state} /> : <ProviderContent data={state.data} />}
    </>
  );
}

function ProviderContent({ data }: { data: EvaluationViewModel }) {
  const stats = prepareProviderStatistics(data);
  const degraded = stats.fallbacks > 0;
  return (
    <div className="space-y-[22px]">
      <DiagnosticRunNotice data={data} />
      {degraded ? <SystemMessage variant="warning" title="Answer provider degraded">The evidence pipeline remained answer-ready, but one or more generated answers were replaced by citation-only fallback because the configured answer provider was unavailable.</SystemMessage> : null}
      <div className="grid gap-[22px] sm:grid-cols-2 xl:grid-cols-4">
        <QualityCard tier="outcome" label="Primary provider" value={businessLabel(stats.primaryProvider)} interpretation={`Observed models: ${stats.models.join(", ") || "N/A"}`} status="neutral" />
        <QualityCard tier="outcome" label="Supported answer-ready" value={String(stats.eligible)} interpretation="Cases eligible for generated answers" status="info" />
        <QualityCard tier="outcome" label="Generated successfully" value={String(stats.generated)} interpretation={`${stats.fallbacks} citation-only fallback${stats.fallbacks === 1 ? "" : "s"}`} status={degraded ? "warning" : "success"} />
        <QualityCard tier="outcome" label="Generation availability" value={formatEvaluationPercent(stats.availability, stats.eligible)} interpretation={stats.eligible ? `${stats.generated} of ${stats.eligible} generated` : "No applicable cases in this run"} status={stats.availability === null ? "neutral" : degraded ? "warning" : "success"} />
      </div>
      <div className="grid gap-[22px] lg:grid-cols-2">
        <QualityCard tier="secondary" label="Successful generation latency" value={stats.generatedLatency} interpretation="Client-observed end-to-end latency for generated answers." />
        <QualityCard tier="secondary" label="Citation-only fallback latency" value={stats.fallbackLatency} interpretation="Client-observed end-to-end latency for answer-ready provider fallback." />
      </div>
      <QualityCard tier="secondary"><h2 className="text-base font-semibold text-neutral-900">Generation error categories</h2>{stats.errorCategories.length ? <ul className="mt-4 space-y-2">{stats.errorCategories.map((item) => <li key={item.name} className="flex items-center justify-between gap-3 border-t border-neutral-200 pt-2 first:border-0 first:pt-0"><span className="text-sm text-neutral-700">{businessLabel(item.name)}</span><span className="font-metric text-sm font-semibold text-neutral-900">{item.count}</span></li>)}</ul> : <p className="mt-3 text-sm text-neutral-600">No provider generation failures were recorded.</p>}</QualityCard>
    </div>
  );
}
