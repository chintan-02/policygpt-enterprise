import type { EvaluationViewModel, OutcomeCardView } from "./evaluation";
import { formatEvaluationPercent } from "../formatters/evaluation";
import type { FrontendHealthResponse, FrontendReadinessResponse } from "../api/types";

export type OverviewEvaluationState =
  | "loading"
  | "not_found"
  | "invalid"
  | "unavailable";

export function coreEvidencePresentation(
  health: FrontendHealthResponse,
  readiness: FrontendReadinessResponse,
) {
  const ready =
    health.backendReachable &&
    readiness.status === "ready" &&
    readiness.database === "ready" &&
    readiness.vectorStore === "ready";
  return {
    ready,
    value: ready ? "Ready" : "Unavailable",
    status: ready ? ("operational" as const) : ("unavailable" as const),
    statusLabel: ready ? "Ready" : "Unavailable",
    description: ready
      ? "FastAPI, PostgreSQL metadata, and Chroma evidence retrieval are ready."
      : "A required evidence service is unavailable. Review System for details.",
  };
}

export function answerGenerationPresentation(
  readiness: FrontendReadinessResponse,
) {
  if (readiness.provider === "configured") {
    return {
      value: "Available",
      status: "operational" as const,
      statusLabel: "Ready",
      description: "Configured answer generation is available.",
    };
  }
  if (readiness.provider === "citation_only_fallback") {
    return {
      value: "Citation-only",
      status: "degraded" as const,
      statusLabel: "Degraded",
      description:
        "Generated answers are unavailable, but verified evidence remains accessible.",
    };
  }
  if (readiness.provider === "unavailable") {
    return {
      value: "Unavailable",
      status: "degraded" as const,
      statusLabel: "Degraded",
      description:
        "Generated answers are unavailable, but verified evidence remains accessible.",
    };
  }
  return {
    value: "Unknown",
    status: "degraded" as const,
    statusLabel: "Degraded",
    description:
      "Generated-answer availability could not be verified, but it does not change evidence-service readiness.",
  };
}

const placeholderCopy: Record<
  OverviewEvaluationState,
  { value: string; description: string }
> = {
  loading: {
    value: "Loading latest evaluation",
    description: "Checking the latest read-only evaluation artifact.",
  },
  not_found: {
    value: "No evaluation run loaded",
    description: "Run or load an evaluation artifact to view this metric.",
  },
  invalid: {
    value: "Evaluation artifact invalid",
    description: "The latest artifact could not be safely validated.",
  },
  unavailable: {
    value: "Evaluation unavailable",
    description: "The latest evaluation artifact could not be reached safely.",
  },
};

export function prepareOverviewEvaluationCards(
  data: EvaluationViewModel,
): OutcomeCardView[] {
  const answerReady = data.results.filter(
    (item) => item.should_answer && item.answer_ready && item.diagnostic !== "request_error",
  );
  const generated = answerReady.filter(
    (item) => !item.providerFallbackDetected,
  ).length;

  return [
    {
      key: "retrieval",
      label: "Retrieval page-hit rate",
      value: formatEvaluationPercent(
        data.summary.retrieval_page_hit_rate,
        data.summary.supported_questions,
      ),
      interpretation:
        "Expected policy pages found across supported benchmark cases.",
      status: data.summary.retrieval_page_hit_rate === 1 ? "success" : "error",
    },
    {
      key: "fallback",
      label: "Unsupported fallback accuracy",
      value: formatEvaluationPercent(
        data.summary.fallback_accuracy,
        data.summary.unsupported_questions,
      ),
      interpretation:
        "Unsupported questions were blocked without unsupported citations.",
      status: data.summary.fallback_accuracy === 1 ? "success" : "error",
    },
    {
      key: "readiness",
      label: "Answer-readiness accuracy",
      value: formatEvaluationPercent(
        data.summary.answer_readiness_accuracy,
        data.summary.total_questions,
      ),
      interpretation:
        "Evidence-gating decisions matched the benchmark support labels.",
      status: data.summary.answer_readiness_accuracy === 1 ? "success" : "error",
    },
    {
      key: "generation",
      label: "Generated-answer availability",
      value: `${generated} / ${answerReady.length}`,
      interpretation:
        generated === answerReady.length
          ? "Generated answers were returned for all answer-ready cases."
          : "Citation-only fallback was used because generation was unavailable.",
      status:
        answerReady.length === 0
          ? "neutral"
          : generated === answerReady.length
            ? "success"
            : "warning",
    },
  ];
}

export function prepareOverviewEvaluationPlaceholders(
  state: OverviewEvaluationState,
): OutcomeCardView[] {
  const copy = placeholderCopy[state];
  return [
    "Retrieval page-hit rate",
    "Unsupported fallback accuracy",
    "Answer-readiness accuracy",
    "Generated-answer availability",
  ].map((label, index) => ({
    key: `placeholder-${index}`,
    label,
    value: copy.value,
    interpretation: copy.description,
    status: state === "invalid" ? "warning" : state === "unavailable" ? "error" : "neutral",
  }));
}
