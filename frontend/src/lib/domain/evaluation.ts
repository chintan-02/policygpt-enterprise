import type { components } from "../api/generated";
import {
  evaluationArtifactSchema,
  type ParsedEvaluationArtifact,
  type ParsedEvaluationCase,
} from "../validation/evaluation";
import {
  formatEvaluationLatency,
  formatEvaluationPercent,
} from "../formatters/evaluation";

export type GeneratedEvaluationArtifact =
  components["schemas"]["EvaluationArtifactResponse"];

export const diagnosticCategories = [
  "passed_supported_answer",
  "passed_unsupported_fallback",
  "provider_generation_failure",
  "retrieval_page_miss",
  "readiness_mismatch",
  "fallback_guardrail_failure",
  "answer_completeness_failure",
  "numeric_guardrail_rejection",
  "legal_scope_guardrail_rejection",
  "request_error",
  "other_evaluation_failure",
] as const;

export type DiagnosticCategory = (typeof diagnosticCategories)[number];

export type EvaluationCaseView = ParsedEvaluationCase & {
  diagnostic: DiagnosticCategory;
  providerFallbackDetected: boolean;
};

export type EvaluationViewModel = Omit<ParsedEvaluationArtifact, "results"> & {
  results: EvaluationCaseView[];
};

export type GateStatus = "passed" | "needs_attention" | "not_applicable";

export type QualityGateView = {
  key: string;
  label: string;
  status: GateStatus;
  value: string;
  description: string;
};

export type OutcomeCardView = {
  key: string;
  label: string;
  value: string;
  interpretation: string;
  status: "success" | "warning" | "error" | "neutral";
  statusLabel?: string;
};

export type EvaluationFilters = {
  status?: string;
  support?: string;
  diagnostic?: string;
  category?: string;
  search?: string;
  difficulty?: string;
  evidence?: string;
  provider?: string;
  fallback?: string;
  numericMismatch?: string;
  scopeRisk?: string;
  directSupport?: string;
};

export function providerFallbackDetected(evaluationCase: ParsedEvaluationCase): boolean {
  return (
    evaluationCase.provider_fallback_used === true ||
    (evaluationCase.should_answer &&
      evaluationCase.answer_ready &&
      evaluationCase.fallback_used &&
      evaluationCase.citation_count > 0)
  );
}

export function classifyEvaluationCase(
  evaluationCase: ParsedEvaluationCase,
): DiagnosticCategory {
  if (evaluationCase.error_type) return "request_error";
  if (evaluationCase.case_passed && evaluationCase.should_answer) {
    return "passed_supported_answer";
  }
  if (evaluationCase.case_passed && !evaluationCase.should_answer) {
    return "passed_unsupported_fallback";
  }
  if (providerFallbackDetected(evaluationCase)) return "provider_generation_failure";
  if (!evaluationCase.readiness_correct) return "readiness_mismatch";
  if (!evaluationCase.should_answer && evaluationCase.fallback_correct === false) {
    return "fallback_guardrail_failure";
  }
  if (evaluationCase.should_answer && evaluationCase.page_hit === false) {
    return "retrieval_page_miss";
  }
  if (evaluationCase.should_answer && evaluationCase.missing_keywords.length > 0) {
    return "answer_completeness_failure";
  }
  if (evaluationCase.numeric_mismatch || evaluationCase.confidence_breakdown?.numeric_mismatch) {
    return "numeric_guardrail_rejection";
  }
  if (evaluationCase.scope_risk || evaluationCase.confidence_breakdown?.scope_risk) {
    return "legal_scope_guardrail_rejection";
  }
  return "other_evaluation_failure";
}

export function adaptEvaluationArtifact(value: unknown): EvaluationViewModel {
  const parsed = evaluationArtifactSchema.parse(value);
  const generatedContract: GeneratedEvaluationArtifact = parsed;
  void generatedContract;

  if (
    parsed.artifact.question_count !== parsed.results.length ||
    parsed.run.question_count !== parsed.summary.total_questions ||
    parsed.summary.total_questions !== parsed.results.length
  ) {
    throw new Error("Evaluation question counts do not agree.");
  }

  return {
    ...parsed,
    results: parsed.results.map((evaluationCase) => ({
      ...evaluationCase,
      diagnostic: classifyEvaluationCase(evaluationCase),
      providerFallbackDetected: providerFallbackDetected(evaluationCase),
    })),
  };
}

function ratioOutcome(
  key: string,
  label: string,
  numerator: number,
  denominator: number,
  officialValue: number,
  successText: string,
): OutcomeCardView {
  if (denominator === 0) {
    return {
      key,
      label,
      value: "N/A",
      interpretation: "No applicable cases in this run",
      status: "neutral",
      statusLabel: "Not applicable",
    };
  }
  const status = numerator === denominator ? "success" : "error";
  return {
    key,
    label,
    value: formatEvaluationPercent(officialValue),
    interpretation: successText,
    status,
  };
}

export function prepareOutcomeCards(data: EvaluationViewModel): OutcomeCardView[] {
  const supported = data.results.filter(
    (item) => item.should_answer && item.diagnostic !== "request_error",
  );
  const unsupported = data.results.filter((item) => !item.should_answer);
  const generatedCompletenessCases = data.results.filter(
    (item) =>
      item.should_answer &&
      item.answer_ready &&
      !item.providerFallbackDetected &&
      !item.fallback_used &&
      item.diagnostic !== "request_error" &&
      !item.error_type &&
      item.answer.trim().length > 0 &&
      item.keyword_match_score !== null &&
      item.keyword_match_score !== undefined,
  );
  const providerCases = data.results.filter(
    (item) => item.should_answer && item.answer_ready && item.diagnostic !== "request_error",
  );
  const generated = providerCases.filter((item) => !item.providerFallbackDetected).length;
  // The evaluator owns keyword scoring. The frontend only scopes its existing
  // per-case scores to answers that were actually generated, then aggregates them.
  const completenessScore = generatedCompletenessCases.length
    ? generatedCompletenessCases.reduce(
        (total, item) => total + (item.keyword_match_score ?? 0),
        0,
      ) / generatedCompletenessCases.length
    : null;

  return [
    ratioOutcome(
      "evidence",
      "Evidence Quality",
      supported.filter((item) => item.page_hit === true).length,
      supported.length,
      data.summary.retrieval_page_hit_rate,
      "Expected policy pages found",
    ),
    ratioOutcome(
      "safety",
      "Safety",
      unsupported.filter((item) => item.fallback_correct === true).length,
      unsupported.length,
      data.summary.fallback_accuracy,
      "Unsupported questions safely blocked",
    ),
    completenessScore === null
      ? {
          key: "completeness",
          label: "Answer Completeness",
          value: "N/A",
          interpretation:
            "No generated answers were available for completeness scoring.",
          status: "neutral",
          statusLabel: "Not applicable",
        }
      : {
          key: "completeness",
          label: "Answer Completeness",
          value: formatEvaluationPercent(completenessScore),
          interpretation: "Expected policy details included",
          status: completenessScore === 1 ? "success" : "error",
        },
    providerCases.length === 0
      ? {
          key: "provider",
          label: "Provider Availability",
          value: "N/A",
          interpretation: "No applicable cases in this run",
          status: "neutral",
          statusLabel: "Not applicable",
        }
      : {
          key: "provider",
          label: "Provider Availability",
          value: generated === providerCases.length ? "Operational" : "Degraded",
          interpretation:
            generated === providerCases.length
              ? `${generated} of ${providerCases.length} answers generated`
              : `${providerCases.length - generated} citation-only fallback${providerCases.length - generated === 1 ? "" : "s"} detected`,
          status: generated === providerCases.length ? "success" : "warning",
        },
  ];
}

function gate(
  key: string,
  label: string,
  passed: boolean,
  value: string,
  description: string,
): QualityGateView {
  return {
    key,
    label,
    status: passed ? "passed" : "needs_attention",
    value,
    description,
  };
}

export function prepareQualityGates(data: EvaluationViewModel): QualityGateView[] {
  const supported = data.results.filter(
    (item) => item.should_answer && item.diagnostic !== "request_error",
  );
  const providerCases = supported.filter((item) => item.answer_ready);
  const generated = providerCases.filter((item) => !item.providerFallbackDetected).length;
  const gates: QualityGateView[] = [
    gate(
      "request-errors",
      "Request errors",
      data.summary.request_error_count === 0,
      String(data.summary.request_error_count),
      "Evaluation transport and response processing should complete without errors.",
    ),
    gate(
      "readiness",
      "Answer-readiness accuracy",
      data.summary.total_questions > 0 && data.summary.answer_readiness_accuracy === 1,
      formatEvaluationPercent(data.summary.answer_readiness_accuracy, data.summary.total_questions),
      "Evidence gating should match benchmark support labels.",
    ),
  ];

  gates.push(
    data.summary.unsupported_questions === 0
      ? {
          key: "fallback",
          label: "Unsupported fallback accuracy",
          status: "not_applicable",
          value: "N/A",
          description: "No unsupported cases were evaluated in this run.",
        }
      : gate(
          "fallback",
          "Unsupported fallback accuracy",
          data.summary.fallback_accuracy === 1,
          formatEvaluationPercent(data.summary.fallback_accuracy),
          "Unsupported questions should be blocked without citations.",
        ),
  );

  gates.push(
    supported.length === 0
      ? {
          key: "retrieval",
          label: "Retrieval page-hit rate",
          status: "not_applicable",
          value: "N/A",
          description: "No supported cases were available for retrieval scoring.",
        }
      : gate(
          "retrieval",
          "Retrieval page-hit rate",
          data.summary.retrieval_page_hit_rate === 1,
          formatEvaluationPercent(data.summary.retrieval_page_hit_rate),
          "Supported cases should cite an expected policy page.",
        ),
  );

  gates.push(
    gate(
      "duplicates",
      "Duplicate citation warning",
      !data.run.duplicate_citation_warning,
      String(data.run.duplicate_citation_warning),
      "Repeated citation identities should not occur.",
    ),
  );

  gates.push(
    providerCases.length === 0
      ? {
          key: "provider",
          label: "Generated-answer availability",
          status: "not_applicable",
          value: "N/A",
          description: "No supported answer-ready cases were evaluated.",
        }
      : gate(
          "provider",
          "Generated-answer availability",
          generated === providerCases.length,
          `${generated} / ${providerCases.length}`,
          "Provider generation is measured separately from evidence retrieval.",
        ),
  );

  return gates;
}

export function prepareOperationalSummary(data: EvaluationViewModel): string {
  const evidencePassed =
    data.summary.supported_questions === 0 || data.summary.retrieval_page_hit_rate === 1;
  const safetyPassed =
    data.summary.unsupported_questions === 0 || data.summary.fallback_accuracy === 1;
  const providerFallbacks = data.results.filter((item) => item.providerFallbackDetected).length;
  const statements: string[] = [];
  if (evidencePassed && data.summary.supported_questions > 0) {
    statements.push("Evidence retrieval found the expected policy pages.");
  }
  if (safetyPassed && data.summary.unsupported_questions > 0) {
    statements.push("Unsupported-answer safety passed.");
  }
  if (providerFallbacks > 0) {
    statements.push(
      "The answer provider was unavailable for at least one answer-ready case, so citation-only fallback was used without changing the retrieval result.",
    );
  }
  if (data.summary.failed_questions_count > 0 && providerFallbacks === 0) {
    statements.push("One or more benchmark cases require review.");
  }
  return statements.join(" ") || "This run contains no applicable benchmark outcomes.";
}

export function shouldRenderEvaluationCharts(data: EvaluationViewModel): boolean {
  return data.results.length >= 3;
}

export function groupCasesBy(
  cases: EvaluationCaseView[],
  key: "category" | "difficulty" | "evidence_status" | "llm_provider" | "diagnostic",
): Array<{ name: string; passed: number; review: number; total: number }> {
  const groups = new Map<string, { passed: number; review: number; total: number }>();
  for (const evaluationCase of cases) {
    const name = evaluationCase[key];
    const current = groups.get(name) ?? { passed: 0, review: 0, total: 0 };
    current.total += 1;
    if (evaluationCase.case_passed) current.passed += 1;
    else current.review += 1;
    groups.set(name, current);
  }
  return [...groups.entries()]
    .map(([name, values]) => ({ name, ...values }))
    .sort((left, right) => left.name.localeCompare(right.name));
}

function filterBoolean(value: string | undefined, actual: boolean | null | undefined): boolean {
  if (!value || value === "all") return true;
  return actual === (value === "true");
}

export function filterEvaluationCases(
  cases: EvaluationCaseView[],
  filters: EvaluationFilters,
): EvaluationCaseView[] {
  const search = filters.search?.trim().toLowerCase();
  return cases
    .filter((item) => !filters.status || filters.status === "all" || (filters.status === "passed" ? item.case_passed : !item.case_passed))
    .filter((item) => !filters.support || filters.support === "all" || (filters.support === "supported" ? item.should_answer : !item.should_answer))
    .filter((item) => !filters.diagnostic || filters.diagnostic === "all" || item.diagnostic === filters.diagnostic)
    .filter((item) => !filters.category || filters.category === "all" || item.category === filters.category)
    .filter((item) => !filters.difficulty || filters.difficulty === "all" || item.difficulty === filters.difficulty)
    .filter((item) => !filters.evidence || filters.evidence === "all" || item.evidence_status === filters.evidence)
    .filter((item) => !filters.provider || filters.provider === "all" || item.llm_provider === filters.provider)
    .filter((item) => filterBoolean(filters.fallback, item.fallback_used))
    .filter((item) => filterBoolean(filters.numericMismatch, item.numeric_mismatch))
    .filter((item) => filterBoolean(filters.scopeRisk, item.scope_risk))
    .filter((item) => filterBoolean(filters.directSupport, item.direct_support))
    .filter((item) => !search || `${item.id} ${item.question} ${item.category}`.toLowerCase().includes(search))
    .sort((left, right) => Number(left.case_passed) - Number(right.case_passed) || left.id.localeCompare(right.id));
}

export function selectCaseFromSearch(
  cases: EvaluationCaseView[],
  caseId: string | null | undefined,
): EvaluationCaseView | null {
  if (!caseId) return null;
  return cases.find((item) => item.id === caseId) ?? null;
}

export function prepareProviderStatistics(data: EvaluationViewModel) {
  const eligible = data.results.filter(
    (item) => item.should_answer && item.answer_ready && item.diagnostic !== "request_error",
  );
  const generated = eligible.filter((item) => !item.providerFallbackDetected);
  const fallbacks = eligible.filter((item) => item.providerFallbackDetected);
  const providers = [...new Set(data.results.map((item) => item.llm_provider))];
  const models = [...new Set(data.results.map((item) => item.model_name).filter(Boolean))] as string[];
  const average = (cases: EvaluationCaseView[]) =>
    cases.length ? cases.reduce((sum, item) => sum + item.latency_ms, 0) / cases.length : null;
  const errorCategories = groupCasesBy(fallbacks, "diagnostic").map((item) => ({
    name: item.name,
    count: item.total,
  }));
  return {
    primaryProvider: providers[0] ?? "N/A",
    providers,
    models,
    eligible: eligible.length,
    generated: generated.length,
    fallbacks: fallbacks.length,
    availability: eligible.length ? generated.length / eligible.length : null,
    generatedLatency: formatEvaluationLatency(average(generated)),
    fallbackLatency: formatEvaluationLatency(average(fallbacks)),
    errorCategories,
  };
}

export function prepareConfidenceStatistics(data: EvaluationViewModel) {
  const score = (item: EvaluationCaseView, key: "answerability_score" | "top_retrieval_score" | "lexical_coverage") =>
    item[key] ?? item.confidence_breakdown?.[key] ?? null;
  const answerability = data.results.map((item) => score(item, "answerability_score")).filter((value): value is number => value !== null);
  const questionCoverage = data.results.map((item) => score(item, "lexical_coverage")).filter((value): value is number => value !== null);
  const retrievalStrength = data.results.map((item) => score(item, "top_retrieval_score")).filter((value): value is number => value !== null);
  const directSupport = data.results.map((item) => item.direct_support ?? item.confidence_breakdown?.direct_support).filter((value): value is boolean => value !== null && value !== undefined);
  const average = (values: number[]) => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
  const confidenceGroups = new Map<string, number[]>();
  for (const item of data.results) {
    const values = confidenceGroups.get(item.diagnostic) ?? [];
    values.push(item.confidence_score);
    confidenceGroups.set(item.diagnostic, values);
  }
  return {
    averageAnswerability: average(answerability),
    averageQuestionCoverage: average(questionCoverage),
    averageRetrievalStrength: average(retrievalStrength),
    directSupportRate: directSupport.length ? directSupport.filter(Boolean).length / directSupport.length : null,
    directSupportCount: directSupport.length,
    numericMismatchCount: data.results.filter((item) => item.numeric_mismatch || item.confidence_breakdown?.numeric_mismatch).length,
    scopeRiskCount: data.results.filter((item) => item.scope_risk || item.confidence_breakdown?.scope_risk).length,
    evidenceDistribution: groupCasesBy(data.results, "evidence_status"),
    confidenceByOutcome: [...confidenceGroups.entries()].map(([name, values]) => ({
      name,
      score: average(values) ?? 0,
    })),
    topRetrievalScores: data.results.map((item) => ({
      name: item.id,
      score: score(item, "top_retrieval_score"),
    })).filter((item): item is { name: string; score: number } => item.score !== null),
  };
}
