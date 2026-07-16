import { Activity, Bot, SearchCheck, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/system/page-header";
import { QualityCard } from "@/components/policygpt/quality-card";
import { StatusPill } from "@/components/policygpt/status-pill";
import { getBackendHealth } from "@/lib/api/health";
import { titleCase } from "@/lib/formatters";

export default async function OverviewPage() {
  const health = await getBackendHealth();
  const operationalCopy = health.backendReachable
    ? "The Ask workspace is connected to the live FastAPI evidence pipeline. Answers are shown only when the backend returns citation-backed support."
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
    </>
  );
}
