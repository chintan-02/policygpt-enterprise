import type { components } from "../api/generated";
import {
  evaluationArtifactSchema,
  type ParsedEvaluationArtifact,
  type ParsedEvaluationCase,
} from "../validation/evaluation";
import {
  evaluationLabel,
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
  statusLabel?: string;
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

export type EvaluationCasePresentation = {
  evidence: { label: string; status: "success" | "warning" | "error" | "neutral" };
  safety: { label: string; status: "success" | "warning" | "error" | "neutral" };
  provider: { label: string; status: "success" | "warning" | "error" | "neutral" };
  overall: { label: string; status: "success" | "warning" | "error" };
};

export type EvaluationIssueGroup = {
  key: string;
  title: string;
  count: number;
  description: string;
  href: string;
  caseIds: string[];
  status: "warning" | "error";
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
  const providerCases = data.results.filter(
    (item) => item.should_answer && item.answer_ready && item.diagnostic !== "request_error",
  );
  const generated = providerCases.filter((item) => !item.providerFallbackDetected).length;
  const readinessMatches = data.results.filter(
    (item) => item.readiness_correct,
  ).length;

  return [
    ratioOutcome(
      "evidence",
      "Retrieval page-hit rate",
      supported.filter((item) => item.page_hit === true).length,
      supported.length,
      data.summary.retrieval_page_hit_rate,
      "Expected policy pages found across supported benchmark cases.",
    ),
    ratioOutcome(
      "safety",
      "Unsupported fallback accuracy",
      unsupported.filter((item) => item.fallback_correct === true).length,
      unsupported.length,
      data.summary.fallback_accuracy,
      "Unsupported questions were blocked without unsupported citations.",
    ),
    ratioOutcome(
      "readiness",
      "Answer-readiness accuracy",
      readinessMatches,
      data.summary.total_questions,
      data.summary.answer_readiness_accuracy,
      "Evidence-gating decisions matched the benchmark support labels.",
    ),
    providerCases.length === 0
      ? {
          key: "generation",
          label: "Generated-answer availability",
          value: "N/A",
          interpretation: "No applicable cases in this run",
          status: "neutral",
          statusLabel: "Not applicable",
        }
      : {
          key: "generation",
          label: "Generated-answer availability",
          value: `${generated} / ${providerCases.length}`,
          interpretation:
            generated === providerCases.length
              ? "Generated answers were returned for all answer-ready cases."
              : `${sentenceStartCount(providerCases.length - generated)} answer-ready case${providerCases.length - generated === 1 ? "" : "s"} used citation-only fallback because generation was unavailable.`,
          status: generated === providerCases.length ? "success" : "warning",
        },
  ];
}

function sentenceStartCount(value: number): string {
  const words = [
    "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
    "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
    "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty",
  ];
  return words[value] ?? String(value);
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

  gates.push({
    key: "duplicates",
    label: "Duplicate citations",
    status: data.run.duplicate_citation_warning ? "needs_attention" : "passed",
    statusLabel: data.run.duplicate_citation_warning ? "Needs review" : "Passed",
    value: data.run.duplicate_citation_warning ? "Detected" : "None detected",
    description: data.run.duplicate_citation_warning
      ? "Repeated citation identities were detected."
      : "No repeated citation identities were detected.",
  });

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
  const providerCases = data.results.filter(
    (item) => item.should_answer && item.answer_ready && item.diagnostic !== "request_error",
  );
  const providerFallbacks = providerCases.filter(
    (item) => item.providerFallbackDetected,
  ).length;
  const statements: string[] = [];
  if (
    evidencePassed &&
    data.summary.supported_questions > 0 &&
    safetyPassed &&
    data.summary.unsupported_questions > 0
  ) {
    statements.push(
      "Evidence retrieval found the expected policy pages and unsupported-answer safety passed.",
    );
  } else if (evidencePassed && data.summary.supported_questions > 0) {
    statements.push("Evidence retrieval found the expected policy pages.");
  } else if (safetyPassed && data.summary.unsupported_questions > 0) {
    statements.push("Unsupported-answer safety passed.");
  }
  if (providerCases.length > 0 && providerFallbacks === providerCases.length) {
    statements.push(
      `All ${providerCases.length} answer-ready cases used citation-only fallback because generated answers were unavailable.`,
    );
  } else if (providerFallbacks > 0) {
    statements.push(
      `${providerFallbacks} of ${providerCases.length} answer-ready cases used citation-only fallback because generated answers were unavailable.`,
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
): Array<{ name: string; passed: number; review: number; failed: number; total: number }> {
  const groups = new Map<string, { passed: number; review: number; failed: number; total: number }>();
  for (const evaluationCase of cases) {
    const name = evaluationCase[key];
    const current = groups.get(name) ?? { passed: 0, review: 0, failed: 0, total: 0 };
    current.total += 1;
    if (evaluationCase.case_passed) current.passed += 1;
    else if (evaluationCase.providerFallbackDetected) current.review += 1;
    else current.failed += 1;
    groups.set(name, current);
  }
  return [...groups.entries()]
    .map(([name, values]) => ({ name: evaluationLabel(name), ...values }))
    .sort((left, right) => right.total - left.total || left.name.localeCompare(right.name));
}

export function evaluationCasePresentation(
  evaluationCase: EvaluationCaseView,
): EvaluationCasePresentation {
  if (
    !evaluationCase.should_answer &&
    evaluationCase.fallback_correct === true &&
    evaluationCase.case_passed
  ) {
    return {
      evidence: { label: "Insufficient evidence", status: "neutral" },
      safety: { label: "Passed unsupported fallback", status: "success" },
      provider: { label: "Not applicable", status: "neutral" },
      overall: { label: "Passed", status: "success" },
    };
  }

  if (
    evaluationCase.should_answer &&
    evaluationCase.answer_ready &&
    evaluationCase.providerFallbackDetected
  ) {
    return {
      evidence: { label: "Answer-ready", status: "success" },
      safety: { label: "Evidence gate passed", status: "success" },
      provider: { label: "Citation-only fallback", status: "warning" },
      overall: { label: "Review provider", status: "warning" },
    };
  }

  if (evaluationCase.case_passed) {
    return {
      evidence: {
        label: evaluationCase.answer_ready ? "Answer-ready" : evaluationLabel(evaluationCase.evidence_status),
        status: "success",
      },
      safety: { label: "Passed", status: "success" },
      provider: { label: "Generated", status: "success" },
      overall: { label: "Passed", status: "success" },
    };
  }

  return {
    evidence: { label: evaluationLabel(evaluationCase.evidence_status), status: "error" },
    safety: { label: "Quality gate failed", status: "error" },
    provider: {
      label: evaluationCase.providerFallbackDetected ? "Citation-only fallback" : "Not completed",
      status: evaluationCase.providerFallbackDetected ? "warning" : "error",
    },
    overall: { label: "Failed", status: "error" },
  };
}

export function prepareEvaluationIssueGroups(
  data: EvaluationViewModel,
): EvaluationIssueGroup[] {
  const groups: EvaluationIssueGroup[] = [];
  const addGroup = (
    key: string,
    title: string,
    description: string,
    href: string,
    cases: EvaluationCaseView[],
    status: "warning" | "error",
  ) => {
    if (!cases.length) return;
    groups.push({
      key,
      title,
      count: cases.length,
      description,
      href,
      caseIds: cases.map((item) => item.id).sort(),
      status,
    });
  };

  addGroup(
    "provider",
    "Provider generation unavailable",
    "answer-ready cases used citation-only fallback.",
    "/evaluations/cases?diagnostic=provider_generation_failure",
    data.results.filter((item) => item.providerFallbackDetected),
    "warning",
  );
  addGroup(
    "requests",
    "Request errors",
    "cases did not complete the evaluation request.",
    "/evaluations/cases?diagnostic=request_error",
    data.results.filter((item) => item.diagnostic === "request_error"),
    "error",
  );
  addGroup(
    "numeric",
    "Numeric mismatch flags",
    "cases contained a structured numeric inconsistency.",
    "/evaluations/cases?numericMismatch=true",
    data.results.filter(
      (item) => item.numeric_mismatch || item.confidence_breakdown?.numeric_mismatch,
    ),
    "warning",
  );
  addGroup(
    "scope",
    "Scope-risk flags",
    "cases were explicitly flagged for policy-scope risk.",
    "/evaluations/cases?scopeRisk=true",
    data.results.filter(
      (item) => item.scope_risk || item.confidence_breakdown?.scope_risk,
    ),
    "warning",
  );
  addGroup(
    "duplicates",
    "Duplicate citations",
    "cases returned repeated citation identities.",
    "/evaluations/cases",
    data.results.filter((item) => item.duplicate_citation_count > 0),
    "error",
  );
  addGroup(
    "retrieval",
    "Retrieval page misses",
    "supported cases did not retrieve an expected policy page.",
    "/evaluations/cases?diagnostic=retrieval_page_miss",
    data.results.filter((item) => item.diagnostic === "retrieval_page_miss"),
    "error",
  );

  return groups;
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
  const answerReadyCases = data.results.filter((item) => item.answer_ready);
  const directSupport = answerReadyCases.map((item) => item.direct_support ?? item.confidence_breakdown?.direct_support).filter((value): value is boolean => value !== null && value !== undefined);
  const average = (values: number[]) => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
  const confidenceGroups = new Map<string, number[]>();
  for (const item of data.results) {
    const values = confidenceGroups.get(item.diagnostic) ?? [];
    values.push(item.confidence_score);
    confidenceGroups.set(item.diagnostic, values);
  }
  return {
    averageSupportedConfidence: data.summary.average_supported_confidence,
    allCaseAverageConfidence: data.summary.average_confidence,
    supportedCaseCount: data.summary.supported_questions,
    answerReadyCount: answerReadyCases.length,
    totalCaseCount: data.summary.total_questions,
    averageAnswerability: average(answerability),
    averageQuestionCoverage: average(questionCoverage),
    averageRetrievalStrength: average(retrievalStrength),
    directSupportRate: directSupport.length ? directSupport.filter(Boolean).length / directSupport.length : null,
    directSupportCount: directSupport.length,
    numericMismatchCount: data.results.filter((item) => item.numeric_mismatch || item.confidence_breakdown?.numeric_mismatch).length,
    scopeRiskCount: data.results.filter((item) => item.scope_risk || item.confidence_breakdown?.scope_risk).length,
    evidenceDistribution: groupCasesBy(data.results, "evidence_status"),
    confidenceByOutcome: [...confidenceGroups.entries()].map(([name, values]) => ({
      name: evaluationLabel(name),
      score: average(values) ?? 0,
    })).sort((left, right) => right.score - left.score),
    topRetrievalScores: data.results.map((item) => ({
      name: item.id,
      score: score(item, "top_retrieval_score"),
    })).filter((item): item is { name: string; score: number } => item.score !== null)
      .sort((left, right) => right.score - left.score),
  };
}
