import {
  ArrowDown,
  ArrowRight,
  CheckCircle2,
  CircleDashed,
} from "lucide-react";
import { PageHeader } from "@/components/system/page-header";
import { QualityCard } from "@/components/policygpt/quality-card";
import { StatusPill } from "@/components/policygpt/status-pill";
import { SystemMessage } from "@/components/policygpt/system-message";
import { getBackendHealth } from "@/lib/api/health";
import { getPublicAppEnvironment } from "@/lib/environment";
import { architectureSteps } from "@/lib/navigation";

const availableCapabilities = [
  "Evidence-backed question workspace connected to the real FastAPI RAG pipeline",
  "PDF extraction and indexing",
  "ChromaDB evidence retrieval",
  "Grounded generation with page-level citations",
  "Calibrated confidence and numeric contradiction guardrails",
  "Legal-scope guardrails and safe citation-only fallback",
  "Structured observability and custom RAG evaluation",
];

const pendingCapabilities = [
  "Persistent document library",
  "Persisted evaluation reporting",
  "Authentication, roles, and multi-tenant controls",
];

export default async function SystemPage() {
  const [health, app] = await Promise.all([
    getBackendHealth(),
    Promise.resolve(getPublicAppEnvironment()),
  ]);

  return (
    <>
      <PageHeader
        title="System"
        description="Review platform connectivity, architecture, and product capability boundaries."
      />

      <div className="grid gap-[22px] lg:grid-cols-3">
        <QualityCard tier="secondary" label="Backend health">
          <StatusPill status={health.status} className="mt-4" />
          <p className="mt-3 text-sm leading-5 text-neutral-600">{health.message}</p>
        </QualityCard>
        <QualityCard tier="secondary" label="Frontend version">
          <div className="font-metric mt-4 text-2xl font-semibold text-neutral-900">
            {app.appVersion}
          </div>
          <p className="mt-3 text-sm text-neutral-500">Phase 14B Ask vertical slice</p>
        </QualityCard>
        <QualityCard tier="secondary" label="Environment">
          <div className="font-metric mt-4 text-2xl font-semibold text-neutral-900">
            {app.appEnvironment}
          </div>
          <p className="mt-3 text-sm text-neutral-500">
            Frontend environment label
          </p>
        </QualityCard>
      </div>

      <section className="mt-8" aria-labelledby="architecture-heading">
        <h2 id="architecture-heading" className="text-lg font-semibold text-neutral-900">
          Evidence pipeline
        </h2>
        <p className="mt-1 text-sm text-neutral-600">
          The governed path from source policy to traceable response.
        </p>
        <QualityCard tier="secondary" className="mt-4">
          <ol className="grid gap-0 md:grid-cols-3 md:gap-x-5 md:gap-y-6 xl:grid-cols-6 xl:gap-4">
            {architectureSteps.map((step, index) => {
              const Icon = step.icon;
              return (
                <li key={step.label} className="relative min-w-0">
                  <div className="flex items-center gap-3 py-1.5 md:flex-col md:items-start md:py-0">
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-teal-100 bg-teal-50 text-teal-700">
                      <Icon aria-hidden="true" size={18} strokeWidth={1.75} />
                    </div>
                    <span className="text-sm leading-5 font-medium text-neutral-700 xl:whitespace-nowrap">
                      {step.label}
                    </span>
                  </div>
                  {index < architectureSteps.length - 1 ? (
                    <>
                      <ArrowDown
                        aria-hidden="true"
                        className="my-0.5 ml-2 text-neutral-500 md:hidden"
                        size={16}
                        strokeWidth={1.75}
                      />
                      <ArrowRight
                        aria-hidden="true"
                        className="absolute top-2 -right-2.5 hidden text-neutral-500 xl:block"
                        size={16}
                        strokeWidth={1.75}
                      />
                    </>
                  ) : null}
                </li>
              );
            })}
          </ol>
        </QualityCard>
      </section>

      <div className="mt-[22px] grid gap-[22px] lg:grid-cols-2">
        <QualityCard tier="secondary">
          <h2 className="text-base font-semibold text-neutral-900">
            Backend capabilities available
          </h2>
          <ul className="mt-4 space-y-3">
            {availableCapabilities.map((capability) => (
              <li key={capability} className="flex gap-2.5 text-sm text-neutral-600">
                <CheckCircle2
                  aria-hidden="true"
                  className="mt-0.5 shrink-0 text-success-700"
                  size={16}
                  strokeWidth={1.75}
                />
                {capability}
              </li>
            ))}
          </ul>
        </QualityCard>
        <QualityCard tier="secondary">
          <h2 className="text-base font-semibold text-neutral-900">
            Product capabilities not yet available
          </h2>
          <ul className="mt-4 space-y-3">
            {pendingCapabilities.map((capability) => (
              <li key={capability} className="flex gap-2.5 text-sm text-neutral-600">
                <CircleDashed
                  aria-hidden="true"
                  className="mt-0.5 shrink-0 text-neutral-400"
                  size={16}
                  strokeWidth={1.75}
                />
                {capability}
              </li>
            ))}
          </ul>
        </QualityCard>
      </div>

      <div className="mt-[22px]">
        <SystemMessage
          variant={health.backendReachable ? "success" : "warning"}
          title={health.backendReachable ? "Backend reachable" : "Backend unavailable"}
        >
          {health.backendReachable
            ? "The interface is using the live FastAPI health result. Provider reliability and evaluation quality are not inferred from configuration."
            : "The console remains available while the backend is offline. Start the FastAPI service and refresh to update this state."}
        </SystemMessage>
      </div>
    </>
  );
}
