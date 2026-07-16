import type { components } from "../api/generated";

export type GeneratedAskResponse =
  components["schemas"]["DocumentAnswerResponse"];
export type GeneratedCitation = components["schemas"]["CitationCard"];
export type GeneratedConfidenceBreakdown =
  components["schemas"]["ConfidenceBreakdown"];

export type AskCompletionState =
  | "completed_supported"
  | "completed_unsupported"
  | "completed_provider_fallback"
  | "invalid_response";

export type EvidenceSupport = "Strong" | "Moderate" | "Limited" | "Insufficient";

export type AskCitation = {
  id: string;
  document: string;
  page: number;
  section: string;
  excerpt: string;
  retrievalScore: number;
  support: EvidenceSupport;
};

export type AskConfidence = {
  score: number;
  status: string;
  label: string;
  reasons: string[];
  breakdown?: GeneratedConfidenceBreakdown;
};

export type AskResult = {
  state: AskCompletionState;
  question: string;
  answer?: string;
  citations: AskCitation[];
  confidence: AskConfidence;
  provider?: string;
  model?: string;
};

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isCitation(value: unknown): value is GeneratedCitation {
  if (!isRecord(value)) return false;

  return (
    typeof value.document_id === "string" &&
    typeof value.filename === "string" &&
    isFiniteNumber(value.page_number) &&
    (value.section_title === undefined ||
      value.section_title === null ||
      typeof value.section_title === "string") &&
    isFiniteNumber(value.chunk_index) &&
    typeof value.excerpt === "string" &&
    isFiniteNumber(value.retrieval_score)
  );
}

function isConfidenceBreakdown(
  value: unknown,
): value is GeneratedConfidenceBreakdown {
  if (!isRecord(value)) return false;

  const numericKeys = [
    "answerability_score",
    "top_retrieval_score",
    "average_retrieval_score",
    "retrieval_margin",
    "lexical_coverage",
    "top_chunk_lexical_coverage",
  ];
  const arrayKeys = [
    "query_numeric_claims",
    "evidence_numeric_claims",
    "missing_numeric_claims",
    "matched_query_terms",
    "missing_query_terms",
    "decision_reasons",
  ];

  return (
    numericKeys.every((key) => isFiniteNumber(value[key])) &&
    (value.numeric_consistency === undefined ||
      value.numeric_consistency === null ||
      isFiniteNumber(value.numeric_consistency)) &&
    typeof value.numeric_mismatch === "boolean" &&
    typeof value.scope_risk === "boolean" &&
    (value.scope_risk_reason === undefined ||
      value.scope_risk_reason === null ||
      typeof value.scope_risk_reason === "string") &&
    typeof value.direct_support === "boolean" &&
    arrayKeys.every((key) => isStringArray(value[key]))
  );
}

/** Runtime guard for the presentation fields used from the generated contract. */
export function isGeneratedAskResponse(value: unknown): value is GeneratedAskResponse {
  if (!isRecord(value)) return false;

  return (
    typeof value.success === "boolean" &&
    typeof value.question === "string" &&
    typeof value.answer === "string" &&
    typeof value.answer_ready === "boolean" &&
    typeof value.evidence_status === "string" &&
    isFiniteNumber(value.confidence_score) &&
    (value.confidence_breakdown === undefined ||
      value.confidence_breakdown === null ||
      isConfidenceBreakdown(value.confidence_breakdown)) &&
    isFiniteNumber(value.citation_count) &&
    Array.isArray(value.citations) &&
    value.citations.every(isCitation) &&
    typeof value.llm_provider === "string" &&
    (value.model_name === undefined ||
      value.model_name === null ||
      typeof value.model_name === "string") &&
    (value.fallback_used === undefined || typeof value.fallback_used === "boolean")
  );
}

function safeFilename(filename: string): string {
  const leaf = filename.split(/[\\/]/).pop()?.trim() ?? "";
  const safe = leaf.replace(/[\u0000-\u001f\u007f]/g, "");
  return safe.slice(0, 160) || "Policy document";
}

function confidenceLabel(status: string): string {
  const normalized = status.trim().toLowerCase();
  const labels: Record<string, string> = {
    strong: "High evidence confidence",
    moderate: "Moderate evidence confidence",
    weak: "Low evidence confidence",
    insufficient: "Insufficient evidence",
  };
  return labels[normalized] ?? "Confidence assessed";
}

function evidenceSupport(status: string): EvidenceSupport {
  const normalized = status.trim().toLowerCase();
  const labels: Record<string, EvidenceSupport> = {
    strong: "Strong",
    moderate: "Moderate",
    weak: "Limited",
    insufficient: "Insufficient",
  };
  return labels[normalized] ?? "Limited";
}

function confidenceReasons(
  breakdown: GeneratedConfidenceBreakdown | null | undefined,
): string[] {
  if (!breakdown) return [];

  const reasons = breakdown.decision_reasons
    .map((reason) => reason.trim())
    .filter(Boolean)
    .slice(0, 3);

  if (reasons.length > 0) return reasons;

  const derived: string[] = [];
  if (breakdown.direct_support) derived.push("Direct policy support was found.");
  if (breakdown.numeric_mismatch) {
    derived.push("A numeric claim did not match the retrieved evidence.");
  }
  if (breakdown.scope_risk) {
    derived.push(
      breakdown.scope_risk_reason?.trim() ||
        "The question may extend beyond the indexed policy scope.",
    );
  }
  return derived;
}

export function adaptAskResponse(value: unknown): AskResult {
  if (!isGeneratedAskResponse(value) || !value.success) {
    return invalidAskResult();
  }

  const fallbackUsed = value.fallback_used === true;
  const citations = value.citations.map((citation, index) => ({
    id: `${citation.document_id}:${citation.page_number}:${citation.chunk_index}:${index}`,
    document: safeFilename(citation.filename),
    page: citation.page_number,
    section: citation.section_title?.trim() || "Policy excerpt",
    excerpt: citation.excerpt.trim(),
    retrievalScore: citation.retrieval_score,
    support: evidenceSupport(value.evidence_status),
  }));

  if (value.answer_ready && citations.length === 0) {
    return invalidAskResult(value.question);
  }

  const state: AskCompletionState = !value.answer_ready
    ? "completed_unsupported"
    : fallbackUsed
      ? "completed_provider_fallback"
      : "completed_supported";

  return {
    state,
    question: value.question.trim(),
    answer: value.answer.trim() || undefined,
    citations,
    confidence: {
      score: Math.min(1, Math.max(0, value.confidence_score)),
      status: value.evidence_status.trim() || "unknown",
      label: confidenceLabel(value.evidence_status),
      reasons: confidenceReasons(value.confidence_breakdown),
      breakdown: value.confidence_breakdown ?? undefined,
    },
    provider:
      value.llm_provider.trim() && value.llm_provider.toLowerCase() !== "none"
        ? value.llm_provider.trim()
        : undefined,
    model: value.model_name?.trim() || undefined,
  };
}

export function invalidAskResult(question = ""): AskResult {
  return {
    state: "invalid_response",
    question,
    citations: [],
    confidence: {
      score: 0,
      status: "invalid",
      label: "Not available",
      reasons: [],
    },
  };
}
