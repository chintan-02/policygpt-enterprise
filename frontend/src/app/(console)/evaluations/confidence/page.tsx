import { OutcomeDistributionChart, ScoreDistributionChart } from "@/components/features/evaluations/evaluation-charts";
import { CompactDiagnostic, DiagnosticRunNotice, EvaluationErrorState } from "@/components/features/evaluations/evaluation-shared";
import { EngineeringPanel } from "@/components/policygpt/engineering-panel";
import { QualityCard } from "@/components/policygpt/quality-card";
import { PageHeader } from "@/components/system/page-header";
import { loadEvaluationPageState } from "@/lib/api/evaluations";
import { prepareConfidenceStatistics, shouldRenderEvaluationCharts, type EvaluationViewModel } from "@/lib/domain/evaluation";
import { formatEvaluationPercent, formatEvaluationScore } from "@/lib/formatters/evaluation";

export default async function EvaluationConfidencePage() {
  const state = await loadEvaluationPageState();
  return (
    <>
      <PageHeader title="Confidence calibration" description="Understand supported-answer confidence, answer-ready coverage, retrieval strength, and explicit safety flags." />
      {state.state === "error" ? <EvaluationErrorState state={state} /> : <ConfidenceContent data={state.data} />}
    </>
  );
}

function ConfidenceContent({ data }: { data: EvaluationViewModel }) {
  const stats = prepareConfidenceStatistics(data);
  const charts = shouldRenderEvaluationCharts(data);
  return (
    <div className="space-y-[22px]">
      <DiagnosticRunNotice data={data} />
      <div className="grid gap-[22px] sm:grid-cols-2 xl:grid-cols-4">
        <QualityCard tier="outcome" label="Average supported confidence" value={formatEvaluationPercent(stats.averageSupportedConfidence, stats.supportedCaseCount)} interpretation={`${stats.supportedCaseCount} supported cases measured`} status={stats.supportedCaseCount ? "info" : "neutral"} />
        <QualityCard tier="outcome" label="Answer-ready cases" value={`${stats.answerReadyCount} / ${stats.totalCaseCount}`} interpretation={`${stats.totalCaseCount - stats.answerReadyCount} cases were intentionally unsupported`} status="info" />
        <QualityCard tier="outcome" label="Numeric mismatch flags" value={String(stats.numericMismatchCount)} interpretation="Cases with structured numeric inconsistency." status={stats.numericMismatchCount ? "warning" : "success"} />
        <QualityCard tier="outcome" label="Scope-risk flags" value={String(stats.scopeRiskCount)} interpretation="Cases explicitly flagged for policy-scope risk." status={stats.scopeRiskCount ? "warning" : "success"} />
      </div>
      <div className="grid gap-[22px] lg:grid-cols-2">
        <QualityCard tier="secondary" label="Answer-ready direct-support coverage" value={formatEvaluationPercent(stats.directSupportRate, stats.directSupportCount)} interpretation={stats.directSupportCount ? `${stats.directSupportCount} answer-ready cases measured` : "No applicable cases in this run"} />
        <QualityCard tier="secondary" label="Question coverage" value={formatEvaluationPercent(stats.averageQuestionCoverage, stats.averageQuestionCoverage === null ? 0 : undefined)} interpretation="Average policy-term coverage across measured cases." />
        <QualityCard tier="secondary" label="Retrieval strength" value={formatEvaluationScore(stats.averageRetrievalStrength, 4)} interpretation="Average top retrieval score, shown as a raw decimal." />
      </div>
      <QualityCard tier="secondary"><h2 className="text-base font-semibold text-neutral-900">How confidence works</h2><p className="mt-2 text-sm leading-6 text-neutral-600">Unsupported benchmark cases intentionally produce insufficient evidence and are excluded from supported-answer confidence. Confidence is based on retrieval strength, question coverage, evidence separation, numeric consistency, and scope guardrails; it is not an LLM self-rating.</p></QualityCard>
      {charts ? <div className="grid gap-[22px] xl:grid-cols-2"><OutcomeDistributionChart title="Evidence-status outcomes" description="Passed and review-required outcomes grouped by evidence confidence." data={stats.evidenceDistribution} /><ScoreDistributionChart title="Top retrieval strength" description="Per-case top retrieval scores shown as raw decimals." data={stats.topRetrievalScores} /><ScoreDistributionChart title="Confidence by outcome" description="Average calibrated confidence grouped by primary diagnostic." data={stats.confidenceByOutcome} /></div> : <CompactDiagnostic data={data} />}
      <EngineeringPanel title="Confidence engineering details"><div className="space-y-3 text-sm leading-6"><p><span className="font-medium text-neutral-700">All-case average confidence:</span> <span className="font-metric">{formatEvaluationPercent(stats.allCaseAverageConfidence, stats.totalCaseCount)}</span></p><p><span className="font-medium text-neutral-700">Average calibrated answerability:</span> <span className="font-metric">{formatEvaluationScore(stats.averageAnswerability, 4)}</span></p><p><span className="font-medium text-neutral-700">Top retrieval observations:</span> {stats.topRetrievalScores.map((item) => `${item.name}: ${formatEvaluationScore(item.score, 4)}`).join(", ") || "N/A"}</p><p>Formula inputs are <span className="font-metric">top_retrieval_score</span>, <span className="font-metric">average_retrieval_score</span>, <span className="font-metric">lexical_coverage</span>, and <span className="font-metric">retrieval_margin</span>, with numeric and scope guardrails.</p></div></EngineeringPanel>
    </div>
  );
}
