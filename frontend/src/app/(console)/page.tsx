import { Activity, Bot, SearchCheck, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/system/page-header";
import { ProvenanceRail } from "@/components/policygpt/provenance-rail";
import { QualityCard } from "@/components/policygpt/quality-card";
import { StatusPill } from "@/components/policygpt/status-pill";
import { SystemMessage } from "@/components/policygpt/system-message";
import { getBackendHealth } from "@/lib/api/health";
import { titleCase } from "@/lib/formatters";

export default async function OverviewPage() {
  const health = await getBackendHealth();
  const operationalCopy = health.backendReachable
    ? "The FastAPI evidence pipeline is reachable. Connect the Ask workspace in Phase 14B to begin evidence-backed policy queries."
    : "The product interface is available, but the FastAPI backend could not be reached. Start the backend on port 8000 and refresh the page.";

  return (
    <>
      <PageHeader
        title="Overview"
        description="Monitor policy intelligence, evidence quality, and platform health."
      />

      <div className="grid gap-[22px] sm:grid-cols-2 xl:grid-cols-4">
        <QualityCard
          tier="outcome"
          label="Platform Health"
          value={titleCase(health.status)}
          status={health.status}
          interpretation={health.message}
          icon={Activity}
        />
        <QualityCard
          tier="outcome"
          label="Evidence Retrieval"
          status="neutral"
          statusLabel="Not evaluated"
          interpretation="Run a full RAG evaluation to calculate evidence quality."
          icon={SearchCheck}
        />
        <QualityCard
          tier="outcome"
          label="Safety Guardrails"
          status="neutral"
          statusLabel="Not evaluated"
          interpretation="Unsupported-answer safety appears after evaluation data is connected."
          icon={ShieldCheck}
        />
        <QualityCard
          tier="outcome"
          label="Answer Provider"
          status="neutral"
          statusLabel="Not measured"
          interpretation="Provider reliability appears after evaluation data is connected."
          icon={Bot}
        />
      </div>

      <QualityCard tier="secondary" className="mt-[22px]">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="max-w-3xl">
            <h2 className="text-base font-semibold text-neutral-900">
              Operational summary
            </h2>
            <p className="mt-2 text-sm leading-6 text-neutral-600">
              {operationalCopy}
            </p>
          </div>
          <StatusPill status={health.status} />
        </div>
      </QualityCard>

      <section className="mt-8" aria-labelledby="foundation-heading">
        <div className="mb-4">
          <div className="text-xs font-semibold tracking-[0.12em] text-teal-700 uppercase">
            Product foundation
          </div>
          <h2 id="foundation-heading" className="mt-2 text-lg font-semibold text-neutral-900">
            Intelligence you can trace
          </h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-neutral-600">
            PolicyGPT pairs every supported answer with a visible path back to its source evidence.
          </p>
        </div>
        <div className="grid gap-[22px] lg:grid-cols-[minmax(0,1.45fr)_minmax(280px,0.55fr)]">
          <QualityCard tier="secondary">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="text-sm font-medium text-neutral-700">
                Provenance rail pattern
              </div>
              <StatusPill status="info" label="Foundation preview" />
            </div>
            <ProvenanceRail
              document="SOURCE"
              page="#"
              section="§ Policy section"
              support="Evidence support"
            />
            <p className="mt-4 text-xs leading-5 text-neutral-500">
              This visual pattern is illustrative only. No citation or evaluation data is shown here.
            </p>
          </QualityCard>
          <SystemMessage variant="info" title="Evidence before answers">
            Answers are presented only when supporting policy evidence is available. Citation-backed Ask integration begins in Phase 14B.
          </SystemMessage>
        </div>
      </section>
    </>
  );
}
