import {
  Activity,
  AppWindow,
  Boxes,
  CheckCircle2,
  CircleDashed,
  Database,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { PageHeader } from "@/components/system/page-header";
import { QualityCard } from "@/components/policygpt/quality-card";
import { StatusPill } from "@/components/policygpt/status-pill";
import { SystemMessage } from "@/components/policygpt/system-message";
import { getBackendHealth } from "@/lib/api/health";
import { getBackendReadiness } from "@/lib/api/readiness";
import { getPublicAppEnvironment } from "@/lib/environment";
import {
  dependencyPresentation,
  deriveSystemOperationalState,
  providerPresentation,
} from "@/lib/domain/system";

const availableCapabilities = [
  "PostgreSQL document identity and ingestion lifecycle metadata",
  "ChromaDB evidence retrieval with page-level provenance",
  "Evidence-gated answers with calibrated confidence",
  "Provider-safe citation-only fallback",
  "Structured request and RAG observability",
  "Read-only evaluation product and release-like Compose deployment",
];

const pendingCapabilities = [
  "Authentication, authorization, and tenant isolation",
  "Managed secrets, backups, TLS termination, and hosted monitoring",
  "Background ingestion workers and multi-replica coordination",
];

function formatCheckedAt(value: string): string {
  const timestamp = new Date(value);
  return Number.isNaN(timestamp.getTime())
    ? "Unknown"
    : timestamp.toLocaleString("en-CA", {
        dateStyle: "medium",
        timeStyle: "medium",
        timeZone: "UTC",
      }) + " UTC";
}

export default async function SystemPage() {
  const [health, readiness, app] = await Promise.all([
    getBackendHealth(),
    getBackendReadiness(),
    Promise.resolve(getPublicAppEnvironment()),
  ]);
  const overall = deriveSystemOperationalState(health, readiness);
  const database = dependencyPresentation(readiness.database);
  const vectorStore = dependencyPresentation(readiness.vectorStore);
  const provider = providerPresentation(readiness.provider);
  const readinessPresentation = dependencyPresentation(
    readiness.status === "ready"
      ? "ready"
      : readiness.status === "not_ready"
        ? "unavailable"
        : "unknown",
  );
  const messageVariant =
    overall.status === "operational"
      ? "success"
      : overall.status === "degraded"
        ? "warning"
        : "error";

  return (
    <>
      <PageHeader
        title="System"
        description="Review live service readiness, provider mode, and operational boundaries."
        actions={
          <a
            href="/system"
            className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 bg-white px-3.5 py-2 text-sm font-semibold text-neutral-700 shadow-xs hover:bg-neutral-50"
          >
            <RefreshCw aria-hidden="true" size={16} strokeWidth={1.75} />
            Refresh
          </a>
        }
      />

      <SystemMessage variant={messageVariant} title={overall.title}>
        {overall.message}
      </SystemMessage>

      <div className="mt-[22px] grid gap-[22px] md:grid-cols-2 xl:grid-cols-3">
        <QualityCard
          tier="outcome"
          label="Frontend"
          icon={AppWindow}
          status="operational"
          statusLabel="Operational"
          interpretation={`Next.js ${app.appVersion} is serving this console in ${app.appEnvironment}.`}
        />
        <QualityCard
          tier="outcome"
          label="Backend liveness"
          icon={Activity}
          status={health.status}
          interpretation={health.message}
        />
        <QualityCard
          tier="outcome"
          label="Backend readiness"
          icon={CheckCircle2}
          status={readinessPresentation.status}
          statusLabel={readinessPresentation.label}
          interpretation={readiness.message}
        />
        <QualityCard
          tier="outcome"
          label="PostgreSQL metadata"
          icon={Database}
          status={database.status}
          statusLabel={database.label}
          interpretation="Required for document identity, duplicate prevention, and ingestion lifecycle metadata."
        />
        <QualityCard
          tier="outcome"
          label="Chroma evidence store"
          icon={Boxes}
          status={vectorStore.status}
          statusLabel={vectorStore.label}
          interpretation="Required for indexed evidence access; readiness never runs a similarity search or embedding."
        />
        <QualityCard
          tier="outcome"
          label="Answer generation"
          icon={Sparkles}
          status={provider.status}
          statusLabel={provider.label}
          interpretation={
            readiness.provider === "configured"
              ? `${readiness.providerName ?? "Configured"} generation is enabled. Provider reachability is not tested from this page.`
              : "Evidence remains available without a provider key or when generation cannot be used."
          }
        />
      </div>

      <QualityCard tier="engineering" className="mt-[22px]">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-neutral-900">Operational check</h2>
            <p className="mt-1 text-sm text-neutral-600">
              Last checked {formatCheckedAt(readiness.checkedAt)}
            </p>
          </div>
          <StatusPill status={overall.status} />
        </div>
        {overall.status !== "operational" && readiness.requestId ? (
          <p className="font-metric mt-3 text-xs text-neutral-500">
            Diagnostic request ID: {readiness.requestId}
          </p>
        ) : null}
      </QualityCard>

      <div className="mt-[22px] grid gap-[22px] lg:grid-cols-2">
        <QualityCard tier="secondary">
          <h2 className="text-base font-semibold text-neutral-900">Implemented boundaries</h2>
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
          <h2 className="text-base font-semibold text-neutral-900">Not yet implemented</h2>
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
    </>
  );
}
