export function formatEvaluationPercent(
  value: number | null | undefined,
  denominator?: number,
): string {
  if (value === null || value === undefined || denominator === 0) return "N/A";
  return `${(value * 100).toFixed(1).replace(".0", "")}%`;
}

export function formatEvaluationScore(
  value: number | null | undefined,
  digits = 2,
): string {
  return value === null || value === undefined ? "N/A" : value.toFixed(digits);
}

export function formatEvaluationLatency(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  return value >= 1000 ? `${(value / 1000).toFixed(2)} s` : `${Math.round(value)} ms`;
}

export function formatEvaluationDate(value: string | null | undefined): string {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "N/A";
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(date);
}

export function formatPages(pages: number[]): string {
  return pages.length ? pages.join(", ") : "None";
}

export function businessLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

const evaluationLabels: Record<string, string> = {
  ai_privacy: "AI Privacy",
  information_security: "Information Security",
  unsupported_private_information: "Unsupported Private Information",
  provider_generation_failure: "Provider unavailable — citation-only fallback",
  passed_unsupported_fallback: "Unsupported fallback passed",
  passed_supported_answer: "Supported answer passed",
  retrieval_page_miss: "Retrieval page miss",
  readiness_mismatch: "Answer-readiness mismatch",
  fallback_guardrail_failure: "Unsupported fallback failed",
  answer_completeness_failure: "Answer completeness failed",
  numeric_guardrail_rejection: "Numeric guardrail rejection",
  legal_scope_guardrail_rejection: "Policy scope guardrail rejection",
  request_error: "Request error",
  other_evaluation_failure: "Evaluation quality gate failed",
};

export function evaluationLabel(value: string): string {
  return evaluationLabels[value] ?? businessLabel(value);
}

export function providerModeLabel(
  provider: string,
  fallbackDetected: boolean,
): string {
  if (fallbackDetected || provider.trim().toLowerCase() === "none") {
    return "Citation-only";
  }
  return businessLabel(provider);
}
