import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { EvaluationViewModel } from "./evaluation";
import {
  answerGenerationPresentation,
  coreEvidencePresentation,
  prepareOverviewEvaluationCards,
  prepareOverviewEvaluationPlaceholders,
} from "./overview";

function latestEvaluation(): EvaluationViewModel {
  const fallbackCase = {
    should_answer: true,
    answer_ready: true,
    diagnostic: "provider_generation_failure",
    providerFallbackDetected: true,
  };
  return {
    summary: {
      total_questions: 16,
      supported_questions: 11,
      unsupported_questions: 5,
      retrieval_page_hit_rate: 1,
      fallback_accuracy: 1,
      answer_readiness_accuracy: 1,
    },
    results: Array.from({ length: 11 }, () => fallbackCase),
  } as unknown as EvaluationViewModel;
}

describe("Overview evaluation presentation", () => {
  it("keeps core evidence services ready during provider fallback", () => {
    const readiness = {
      status: "ready" as const,
      database: "ready" as const,
      vectorStore: "ready" as const,
      provider: "citation_only_fallback" as const,
      message: "Ready",
      checkedAt: "2026-07-16T00:00:00Z",
    };
    const evidence = coreEvidencePresentation(
      {
        status: "operational",
        backendReachable: true,
        serviceName: "PolicyGPT Enterprise",
        message: "Ready",
      },
      readiness,
    );

    expect(evidence).toMatchObject({
      ready: true,
      value: "Ready",
      status: "operational",
      statusLabel: "Ready",
    });
    expect(answerGenerationPresentation(readiness)).toEqual({
      value: "Citation-only",
      status: "degraded",
      statusLabel: "Degraded",
      description:
        "Generated answers are unavailable, but verified evidence remains accessible.",
    });
  });

  it("renders real metrics from a valid latest artifact", () => {
    const cards = prepareOverviewEvaluationCards(latestEvaluation());

    expect(cards).toEqual([
      expect.objectContaining({ label: "Retrieval page-hit rate", value: "100%" }),
      expect.objectContaining({ label: "Unsupported fallback accuracy", value: "100%" }),
      expect.objectContaining({ label: "Answer-readiness accuracy", value: "100%" }),
      expect.objectContaining({
        label: "Generated-answer availability",
        value: "0 / 11",
        status: "warning",
      }),
    ]);
    expect(JSON.stringify(cards)).not.toContain("No evaluation run loaded");
  });

  it.each([
    ["not_found", "No evaluation run loaded"],
    ["invalid", "Evaluation artifact invalid"],
    ["unavailable", "Evaluation unavailable"],
  ] as const)("maps %s to a safe Overview state", (state, value) => {
    expect(prepareOverviewEvaluationPlaceholders(state)).toHaveLength(4);
    expect(prepareOverviewEvaluationPlaceholders(state)[0].value).toBe(value);
  });

  it("uses the read-only evaluation BFF with no-store and exposes refresh", () => {
    const source = readFileSync(
      new URL(
        "../../components/features/evaluations/overview-evaluation-panel.tsx",
        import.meta.url,
      ),
      "utf8",
    );

    expect(source).toContain('fetch("/api/evaluations/latest"');
    expect(source).toContain('cache: "no-store"');
    expect(source).toContain("Refresh evaluation");
    expect(source).toContain("Updated {updatedAt} UTC");
    expect(source).not.toContain("run_eval.py");
  });
});
