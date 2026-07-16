import { Activity, MessageSquareText } from "lucide-react";
import { OverviewEvaluationPanel } from "@/components/features/evaluations/overview-evaluation-panel";
import { PageHeader } from "@/components/system/page-header";
import { QualityCard } from "@/components/policygpt/quality-card";
import { StatusPill } from "@/components/policygpt/status-pill";
import { getBackendHealth } from "@/lib/api/health";
import { getBackendReadiness } from "@/lib/api/readiness";
import { deriveSystemOperationalState } from "@/lib/domain/system";
import {
  answerGenerationPresentation,
  coreEvidencePresentation,
} from "@/lib/domain/overview";

export default async function OverviewPage() {
  const [health, readiness] = await Promise.all([
    getBackendHealth(),
    getBackendReadiness(),
  ]);
  const overall = deriveSystemOperationalState(health, readiness);
  const evidence = coreEvidencePresentation(health, readiness);
  const generation = answerGenerationPresentation(readiness);

  return (
    <>
      <PageHeader
        title="Overview"
        description="Monitor policy intelligence, evidence quality, and platform health."
      />

      <div className="mb-[22px] grid gap-[22px] sm:grid-cols-2">
        <QualityCard
          tier="outcome"
          label="Core evidence services"
          value={evidence.value}
          status={evidence.status}
          statusLabel={evidence.statusLabel}
          interpretation={evidence.description}
          icon={Activity}
        />
        <QualityCard
          tier="outcome"
          label="Answer generation"
          value={generation.value}
          status={generation.status}
          statusLabel={generation.statusLabel}
          interpretation={generation.description}
          icon={MessageSquareText}
        />
      </div>

      <OverviewEvaluationPanel />

      <QualityCard tier="secondary" className="mt-[22px]">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="max-w-3xl">
            <h2 className="text-base font-semibold text-neutral-900">
              Operational summary
            </h2>
            <p className="mt-2 text-sm leading-6 text-neutral-600">
              {overall.message}
            </p>
          </div>
          <StatusPill status={overall.status} />
        </div>
      </QualityCard>
    </>
  );
}
