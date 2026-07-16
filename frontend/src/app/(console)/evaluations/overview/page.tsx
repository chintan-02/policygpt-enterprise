import { AlertTriangle, CalendarClock } from "lucide-react";
import Link from "next/link";
import { OutcomeDistributionChart } from "@/components/features/evaluations/evaluation-charts";
import {
  CompactDiagnostic,
  DiagnosticRunNotice,
  EvaluationErrorState,
  OutcomeCards,
  QualityGates,
} from "@/components/features/evaluations/evaluation-shared";
import { QualityCard } from "@/components/policygpt/quality-card";
import { StatusPill } from "@/components/policygpt/status-pill";
import { PageHeader } from "@/components/system/page-header";
import { loadEvaluationPageState } from "@/lib/api/evaluations";
import {
  groupCasesBy,
  prepareEvaluationIssueGroups,
  prepareOperationalSummary,
  prepareOutcomeCards,
  prepareQualityGates,
  shouldRenderEvaluationCharts,
} from "@/lib/domain/evaluation";
import { formatEvaluationDate } from "@/lib/formatters/evaluation";

export default async function EvaluationOverviewPage() {
  const state = await loadEvaluationPageState();
  return (
    <>
      <PageHeader title="Evaluation overview" description="Monitor evidence retrieval, answer safety, completeness, confidence, and provider reliability across the verified PolicyGPT benchmark." />
      {state.state === "error" ? <EvaluationErrorState state={state} /> : <OverviewContent data={state.data} />}
    </>
  );
}

function OverviewContent({ data }: { data: Extract<Awaited<ReturnType<typeof loadEvaluationPageState>>, { state: "ready" }>["data"] }) {
  const issueGroups = prepareEvaluationIssueGroups(data);
  const hardFailures = issueGroups.some((item) => item.status === "error");
  const providerReview = issueGroups.some((item) => item.key === "provider");
  const charts = shouldRenderEvaluationCharts(data);
  return (
    <div className="space-y-[22px]">
      <DiagnosticRunNotice data={data} />
      <OutcomeCards cards={prepareOutcomeCards(data)} />

      <QualityCard tier="secondary">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="max-w-4xl">
            <h2 className="text-base font-semibold text-neutral-900">Operational summary</h2>
            <p className="mt-2 text-sm leading-6 text-neutral-600">{prepareOperationalSummary(data)}</p>
          </div>
          <StatusPill
            status={hardFailures ? "error" : issueGroups.length ? "warning" : "success"}
            label={hardFailures ? "Quality gate failed" : providerReview ? "Review provider" : issueGroups.length ? "Review required" : "All cases passed"}
          />
        </div>
      </QualityCard>

      <QualityGates gates={prepareQualityGates(data)} />

      {charts ? (
        <OutcomeDistributionChart title="Pass and review by policy category" description="Case outcomes grouped by the benchmark policy category." data={groupCasesBy(data.results, "category")} />
      ) : <CompactDiagnostic data={data} />}

      <div className="grid gap-[22px] lg:grid-cols-2">
        <QualityCard tier="secondary">
          <div className="flex items-center gap-2"><AlertTriangle aria-hidden="true" size={18} className="text-warning-700" /><h2 className="text-base font-semibold text-neutral-900">Issues requiring attention</h2></div>
          {issueGroups.length ? (
            <ul className="mt-4 space-y-4">
              {issueGroups.map((issue) => (
                <li key={issue.key} className="border-t border-neutral-200 pt-4 first:border-0 first:pt-0">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-neutral-900">{issue.title}</h3>
                      <p className="mt-1 text-sm text-neutral-700">
                        <span className="font-metric font-semibold">{issue.count}</span>{" "}
                        {issue.description}
                      </p>
                    </div>
                    <Link href={issue.href} className="text-sm font-semibold text-teal-700 hover:text-teal-900 hover:underline">
                      View filtered cases
                    </Link>
                  </div>
                  <details className="mt-2 text-xs text-neutral-500">
                    <summary className="cursor-pointer font-medium">Affected case IDs</summary>
                    <p className="font-metric mt-2 break-words leading-5">{issue.caseIds.join(", ")}</p>
                  </details>
                </li>
              ))}
            </ul>
          ) : <p className="mt-3 text-sm text-neutral-600">All evaluated cases met the benchmark outcome.</p>}
        </QualityCard>
        <QualityCard tier="secondary">
          <div className="flex items-center gap-2"><CalendarClock aria-hidden="true" size={18} className="text-neutral-500" /><h2 className="text-base font-semibold text-neutral-900">Run coverage</h2></div>
          <div className="font-metric mt-4 text-2xl font-semibold text-neutral-900">{data.artifact.question_count} / {data.artifact.benchmark_question_count ?? data.artifact.question_count}</div>
          <p className="mt-2 text-sm text-neutral-600">{data.artifact.is_partial ? "Diagnostic coverage; not an official benchmark report." : "Full available benchmark coverage."}</p>
          <p className="font-metric mt-4 text-xs text-neutral-500">Artifact updated {formatEvaluationDate(data.artifact.updated_at)} UTC</p>
        </QualityCard>
      </div>
    </div>
  );
}
