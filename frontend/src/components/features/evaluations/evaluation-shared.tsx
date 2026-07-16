import { AlertTriangle, CheckCircle2, CircleMinus, Terminal } from "lucide-react";
import { QualityCard } from "@/components/policygpt/quality-card";
import { StatusPill } from "@/components/policygpt/status-pill";
import { SystemMessage } from "@/components/policygpt/system-message";
import type { EvaluationPageState } from "@/lib/api/evaluations";
import type {
  DiagnosticCategory,
  EvaluationViewModel,
  GateStatus,
  OutcomeCardView,
  QualityGateView,
} from "@/lib/domain/evaluation";
import { businessLabel } from "@/lib/formatters/evaluation";

export function EvaluationErrorState({ state }: { state: Extract<EvaluationPageState, { state: "error" }> }) {
  const missing = state.code === "EVALUATION_NOT_FOUND";
  return (
    <SystemMessage variant={missing ? "info" : state.code === "EVALUATION_INVALID" ? "warning" : "error"} title={state.title}>
      <p>{state.message}</p>
      {missing ? (
        <div className="mt-3 rounded-lg border border-current/15 bg-white/60 p-3 font-mono text-xs leading-6 text-neutral-700">
          <div>python eval/validate_dataset.py</div>
          <div>python eval/run_eval.py --request-delay-seconds 5</div>
        </div>
      ) : (
        <p className="mt-2">The application shell remains available. Check the backend service and artifact, then refresh.</p>
      )}
    </SystemMessage>
  );
}

export function DiagnosticRunNotice({ data }: { data: EvaluationViewModel }) {
  if (!data.artifact.is_partial) return null;
  const benchmark = data.artifact.benchmark_question_count;
  return (
    <div className="mb-5">
      <SystemMessage variant="info" title="Diagnostic run">
        {data.artifact.question_count} of {benchmark ?? "the available"} benchmark cases evaluated. Use this run for debugging, not benchmark reporting.
      </SystemMessage>
    </div>
  );
}

export function OutcomeCards({ cards }: { cards: OutcomeCardView[] }) {
  return (
    <div className="grid gap-[22px] sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <QualityCard
          key={card.key}
          tier="outcome"
          label={card.label}
          value={card.value}
          interpretation={card.interpretation}
          status={card.status}
          statusLabel={card.statusLabel}
        />
      ))}
    </div>
  );
}

const gateStatus: Record<GateStatus, { status: "success" | "warning" | "neutral"; label: string; icon: typeof CheckCircle2 }> = {
  passed: { status: "success", label: "Passed", icon: CheckCircle2 },
  needs_attention: { status: "warning", label: "Needs attention", icon: AlertTriangle },
  not_applicable: { status: "neutral", label: "Not applicable", icon: CircleMinus },
};

export function QualityGates({ gates }: { gates: QualityGateView[] }) {
  return (
    <section aria-labelledby="quality-gates-heading">
      <h2 id="quality-gates-heading" className="text-lg font-semibold text-neutral-900">Production quality gates</h2>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {gates.map((gate) => {
          const presentation = gateStatus[gate.status];
          return (
            <QualityCard key={gate.key} tier="secondary" className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-neutral-900">{gate.label}</h3>
                  <div className="font-metric mt-2 text-xl font-semibold text-neutral-900">{gate.value}</div>
                </div>
                <StatusPill status={presentation.status} label={presentation.label} compact />
              </div>
              <p className="mt-2 text-sm leading-5 text-neutral-600">{gate.description}</p>
            </QualityCard>
          );
        })}
      </div>
    </section>
  );
}

export function DiagnosticPill({ diagnostic }: { diagnostic: DiagnosticCategory }) {
  const passed = diagnostic.startsWith("passed_");
  const provider = diagnostic === "provider_generation_failure";
  return (
    <StatusPill
      compact
      status={passed ? "success" : provider ? "warning" : diagnostic === "request_error" ? "error" : "info"}
      label={businessLabel(diagnostic)}
    />
  );
}

export function CompactDiagnostic({ data }: { data: EvaluationViewModel }) {
  return (
    <QualityCard tier="secondary">
      <div className="flex items-center gap-2 text-neutral-700">
        <Terminal aria-hidden="true" size={18} strokeWidth={1.75} />
        <h2 className="text-base font-semibold text-neutral-900">Case diagnostic</h2>
      </div>
      <div className="mt-4 space-y-3">
        {data.results.map((item) => (
          <div key={item.id} className="flex flex-col gap-2 border-t border-neutral-200 pt-3 first:border-0 first:pt-0 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <div className="font-metric text-xs text-neutral-500">{item.id}</div>
              <p className="mt-1 text-sm text-neutral-700">{item.question}</p>
            </div>
            <DiagnosticPill diagnostic={item.diagnostic} />
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm text-neutral-500">Distribution charts are hidden until at least three cases are available.</p>
    </QualityCard>
  );
}
