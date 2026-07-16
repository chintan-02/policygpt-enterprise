import { describe, expect, it } from "vitest";
import {
  adaptEvaluationArtifact,
  classifyEvaluationCase,
  filterEvaluationCases,
  groupCasesBy,
  prepareOutcomeCards,
  prepareProviderStatistics,
  prepareQualityGates,
  selectCaseFromSearch,
  shouldRenderEvaluationCharts,
} from "./evaluation";
import {
  formatEvaluationDate,
  formatEvaluationPercent,
  formatEvaluationScore,
} from "../formatters/evaluation";

function casePayload(overrides: Record<string, unknown> = {}) {
  return {
    id: "remote_work_001",
    question: "What is the equipment allowance?",
    category: "remote_work",
    difficulty: "easy",
    evaluation_focus: ["retrieval"],
    should_answer: true,
    answer_ready: true,
    readiness_correct: true,
    evidence_status: "strong",
    confidence_score: 0.8,
    confidence_breakdown: {
      answerability_score: 0.8,
      top_retrieval_score: 0.7,
      average_retrieval_score: 0.6,
      retrieval_margin: 0.5,
      lexical_coverage: 0.9,
      top_chunk_lexical_coverage: 0.9,
      numeric_consistency: 1,
      numeric_mismatch: false,
      scope_risk: false,
      direct_support: true,
      decision_reasons: ["Direct evidence was found."],
    },
    expected_pages: [5],
    retrieved_pages: [5],
    page_hit: true,
    expected_answer_keywords: ["CAD 300"],
    matched_keywords: ["CAD 300"],
    missing_keywords: [],
    keyword_match_score: 1,
    answer: "The allowance is CAD 300.",
    fallback_used: false,
    fallback_correct: null,
    citation_count: 1,
    retrieved_filenames: ["sample.pdf"],
    citation_scores: [0.7],
    top_citation_score: 0.7,
    average_citation_score: 0.7,
    duplicate_citation_count: 0,
    latency_ms: 100,
    llm_provider: "groq",
    model_name: "test-model",
    case_passed: true,
    error_type: null,
    ...overrides,
  };
}

function unsupportedCase(overrides: Record<string, unknown> = {}) {
  return casePayload({
    id: "unsupported_001",
    question: "What is a private fact?",
    category: "unsupported",
    difficulty: "moderate",
    should_answer: false,
    answer_ready: false,
    evidence_status: "insufficient",
    confidence_score: 0,
    expected_pages: [],
    retrieved_pages: [],
    page_hit: null,
    expected_answer_keywords: [],
    matched_keywords: [],
    missing_keywords: [],
    keyword_match_score: null,
    answer: "Insufficient evidence.",
    fallback_used: true,
    fallback_correct: true,
    citation_count: 0,
    case_passed: true,
    ...overrides,
  });
}

function artifact(cases = [casePayload()], overrides: Record<string, unknown> = {}) {
  const supported = cases.filter((item) => item.should_answer).length;
  const passed = cases.filter((item) => item.case_passed).length;
  return {
    artifact: {
      updated_at: "2026-07-15T00:00:00Z",
      question_count: cases.length,
      benchmark_question_count: 16,
      is_partial: cases.length < 16,
    },
    run: {
      run_id: "run-123",
      started_at_utc: "2026-07-15T00:00:00Z",
      completed_at_utc: "2026-07-15T00:00:01Z",
      duration_ms: 1000,
      backend_base_label: "Local backend",
      endpoint: "/api/v1/documents/ask",
      dataset_path: "eval/questions.jsonl",
      dataset_sha256: "a".repeat(64),
      top_k: 5,
      timeout_seconds: 60,
      request_delay_seconds: 0,
      question_count: cases.length,
      duplicate_citation_warning: false,
    },
    summary: {
      total_questions: cases.length,
      supported_questions: supported,
      unsupported_questions: cases.length - supported,
      passed_questions: passed,
      failed_questions_count: cases.length - passed,
      request_error_count: cases.filter((item) => item.error_type).length,
      answer_readiness_accuracy: 1,
      fallback_accuracy: cases.some((item) => !item.should_answer) ? 1 : 0,
      retrieval_page_hit_rate: supported ? 1 : 0,
      keyword_match_rate: supported ? 1 : 0,
      average_confidence: 0.8,
      average_supported_confidence: supported ? 0.8 : 0,
      average_latency_ms: 100,
      average_citation_count: supported ? 1 : 0,
    },
    results: cases,
    ...overrides,
  };
}

describe("evaluation artifact adapter", () => {
  it("adapts a valid Step 13 artifact", () => {
    const result = adaptEvaluationArtifact(artifact());
    expect(result.results[0].diagnostic).toBe("passed_supported_answer");
    expect(result.results[0].confidence_breakdown?.answerability_score).toBe(0.8);
  });

  it("normalizes an older Step 12 artifact without confidence fields", () => {
    const older = casePayload();
    delete older.confidence_breakdown;
    const result = adaptEvaluationArtifact(artifact([older]));
    expect(result.results[0].confidence_breakdown).toBeUndefined();
    expect(result.results[0].decision_reasons).toEqual([]);
    expect(result.results[0].numeric_mismatch).toBe(false);
  });

  it("normalizes missing optional collections", () => {
    const sparse = casePayload();
    delete sparse.evaluation_focus;
    delete sparse.retrieved_filenames;
    delete sparse.citation_scores;
    expect(adaptEvaluationArtifact(artifact([sparse])).results[0].citation_scores).toEqual([]);
  });

  it("rejects malformed and count-inconsistent responses", () => {
    expect(() => adaptEvaluationArtifact({ summary: {} })).toThrow();
    expect(() => adaptEvaluationArtifact(artifact([], { results: [casePayload()] }))).toThrow();
  });
});

describe("evaluation classification", () => {
  const diagnostic = (overrides: Record<string, unknown>) =>
    classifyEvaluationCase(adaptEvaluationArtifact(artifact([casePayload(overrides)])).results[0]);

  it("classifies supported and unsupported passes", () => {
    expect(diagnostic({})).toBe("passed_supported_answer");
    const safeUnsupported = adaptEvaluationArtifact(artifact([unsupportedCase({ numeric_mismatch: true })])).results[0];
    expect(safeUnsupported.diagnostic).toBe("passed_unsupported_fallback");
  });

  it("classifies request, provider, readiness, fallback, and retrieval failures", () => {
    expect(diagnostic({ case_passed: false, error_type: "Timeout" })).toBe("request_error");
    expect(diagnostic({ case_passed: false, fallback_used: true })).toBe("provider_generation_failure");
    expect(diagnostic({ case_passed: false, readiness_correct: false })).toBe("readiness_mismatch");
    const fallbackFailure = adaptEvaluationArtifact(artifact([unsupportedCase({ case_passed: false, fallback_correct: false })])).results[0];
    expect(fallbackFailure.diagnostic).toBe("fallback_guardrail_failure");
    expect(diagnostic({ case_passed: false, page_hit: false })).toBe("retrieval_page_miss");
  });

  it("classifies completeness, numeric, scope, and other failures", () => {
    expect(diagnostic({ case_passed: false, missing_keywords: ["approval"] })).toBe("answer_completeness_failure");
    expect(diagnostic({ case_passed: false, numeric_mismatch: true })).toBe("numeric_guardrail_rejection");
    expect(diagnostic({ case_passed: false, scope_risk: true })).toBe("legal_scope_guardrail_rejection");
    expect(diagnostic({ case_passed: false })).toBe("other_evaluation_failure");
  });
});

describe("evaluation selectors", () => {
  it("detects partial and full runs and suppresses one-record charts", () => {
    const partial = adaptEvaluationArtifact(artifact());
    expect(partial.artifact.is_partial).toBe(true);
    expect(shouldRenderEvaluationCharts(partial)).toBe(false);
    const cases = Array.from({ length: 16 }, (_, index) => casePayload({ id: `case_${index}` }));
    const full = adaptEvaluationArtifact(artifact(cases));
    expect(full.artifact.is_partial).toBe(false);
    expect(shouldRenderEvaluationCharts(full)).toBe(true);
  });

  it("uses N/A for zero denominator outcome cards", () => {
    const result = adaptEvaluationArtifact(artifact([casePayload()]));
    expect(prepareOutcomeCards(result).find((item) => item.key === "safety")?.value).toBe("N/A");
    expect(formatEvaluationPercent(0, 0)).toBe("N/A");
  });

  it("shows completeness as not applicable for one provider fallback", () => {
    const result = adaptEvaluationArtifact(artifact([
      casePayload({
        case_passed: false,
        fallback_used: true,
        keyword_match_score: 0,
      }),
    ]));

    const completeness = prepareOutcomeCards(result).find(
      (item) => item.key === "completeness",
    );

    expect(completeness).toMatchObject({
      value: "N/A",
      status: "neutral",
      statusLabel: "Not applicable",
      interpretation:
        "No generated answers were available for completeness scoring.",
    });
  });

  it("shows completeness as not applicable for several provider fallbacks", () => {
    const result = adaptEvaluationArtifact(artifact([
      casePayload({ id: "fallback_1", case_passed: false, fallback_used: true, keyword_match_score: 0 }),
      casePayload({ id: "fallback_2", case_passed: false, fallback_used: true, keyword_match_score: 0 }),
      casePayload({ id: "fallback_3", case_passed: false, fallback_used: true, keyword_match_score: 0 }),
    ]));

    expect(
      prepareOutcomeCards(result).find((item) => item.key === "completeness")?.value,
    ).toBe("N/A");
  });

  it("uses the artifact completeness score for a generated answer", () => {
    const result = adaptEvaluationArtifact(artifact([
      casePayload({
        case_passed: false,
        keyword_match_score: 0.6,
        matched_keywords: ["CAD 300"],
        missing_keywords: ["approval"],
      }),
    ]));

    expect(
      prepareOutcomeCards(result).find((item) => item.key === "completeness")?.value,
    ).toBe("60%");
  });

  it("limits mixed-run completeness to successfully generated answers", () => {
    const result = adaptEvaluationArtifact(artifact([
      casePayload({
        id: "generated",
        case_passed: false,
        keyword_match_score: 0.5,
        missing_keywords: ["approval"],
      }),
      casePayload({
        id: "provider_fallback",
        case_passed: false,
        fallback_used: true,
        keyword_match_score: 0,
      }),
    ]));
    const cards = prepareOutcomeCards(result);

    expect(cards.find((item) => item.key === "completeness")?.value).toBe("50%");
    expect(cards.find((item) => item.key === "evidence")).toMatchObject({
      value: "100%",
      status: "success",
    });
  });

  it("shows completeness as not applicable when there are no supported cases", () => {
    const result = adaptEvaluationArtifact(artifact([unsupportedCase()]));

    expect(
      prepareOutcomeCards(result).find((item) => item.key === "completeness"),
    ).toMatchObject({ value: "N/A", statusLabel: "Not applicable" });
  });

  it("does not let provider fallback fail evidence quality", () => {
    const result = adaptEvaluationArtifact(artifact([
      casePayload({ case_passed: false, fallback_used: true, keyword_match_score: 0 }),
    ]));

    expect(
      prepareOutcomeCards(result).find((item) => item.key === "evidence"),
    ).toMatchObject({ value: "100%", status: "success" });
  });

  it("prepares quality gates and keeps provider fallback independent", () => {
    const fallback = casePayload({ case_passed: false, fallback_used: true });
    const result = adaptEvaluationArtifact(artifact([fallback]));
    const gates = prepareQualityGates(result);
    expect(gates.find((item) => item.key === "retrieval")?.status).toBe("passed");
    expect(gates.find((item) => item.key === "provider")?.status).toBe("needs_attention");
  });

  it("calculates provider availability from eligible cases", () => {
    const result = adaptEvaluationArtifact(artifact([
      casePayload({ id: "generated" }),
      casePayload({ id: "fallback", case_passed: false, fallback_used: true }),
      unsupportedCase(),
    ]));
    const provider = prepareProviderStatistics(result);
    expect(provider.eligible).toBe(2);
    expect(provider.generated).toBe(1);
    expect(provider.fallbacks).toBe(1);
    expect(provider.availability).toBe(0.5);
  });

  it("filters and combines filters deterministically", () => {
    const result = adaptEvaluationArtifact(artifact([
      casePayload(),
      casePayload({ id: "expense_001", category: "expenses", difficulty: "hard", case_passed: false, numeric_mismatch: true }),
      unsupportedCase(),
    ]));
    expect(filterEvaluationCases(result.results, { category: "expenses" })).toHaveLength(1);
    expect(filterEvaluationCases(result.results, { status: "review", difficulty: "hard", numericMismatch: "true", search: "expense" }).map((item) => item.id)).toEqual(["expense_001"]);
  });

  it("groups chart data and selects drawer cases from URL state", () => {
    const result = adaptEvaluationArtifact(artifact([casePayload(), unsupportedCase()]));
    expect(groupCasesBy(result.results, "category")).toEqual([
      { name: "remote_work", passed: 1, review: 0, total: 1 },
      { name: "unsupported", passed: 1, review: 0, total: 1 },
    ]);
    expect(selectCaseFromSearch(result.results, "unsupported_001")?.id).toBe("unsupported_001");
    expect(selectCaseFromSearch(result.results, "missing")).toBeNull();
  });

  it("formats unsafe or absent values without leaking implementation detail", () => {
    expect(formatEvaluationDate("not-a-date")).toBe("N/A");
    expect(formatEvaluationScore(null)).toBe("N/A");
    expect(formatEvaluationScore(0.6471, 4)).toBe("0.6471");
  });
});
