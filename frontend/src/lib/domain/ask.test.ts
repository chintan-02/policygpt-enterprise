import { describe, expect, it } from "vitest";
import type { GeneratedAskResponse } from "./ask";
import { adaptAskResponse } from "./ask";

const breakdown = {
  answerability_score: 0.84,
  top_retrieval_score: 0.79,
  average_retrieval_score: 0.65,
  retrieval_margin: 0.14,
  lexical_coverage: 0.8,
  top_chunk_lexical_coverage: 0.75,
  numeric_consistency: null,
  numeric_mismatch: false,
  query_numeric_claims: [],
  evidence_numeric_claims: [],
  missing_numeric_claims: [],
  scope_risk: false,
  scope_risk_reason: null,
  matched_query_terms: ["leave"],
  missing_query_terms: [],
  direct_support: true,
  decision_reasons: ["Direct evidence supports the requested policy detail."],
};

function supportedResponse(
  overrides: Partial<GeneratedAskResponse> = {},
): GeneratedAskResponse {
  return {
    success: true,
    question: "What is the leave policy?",
    answer: "Eligible employees receive policy-defined leave.",
    answer_ready: true,
    evidence_status: "strong",
    confidence_score: 0.84,
    confidence_breakdown: breakdown,
    citation_count: 1,
    citations: [
      {
        document_id: "leave-policy",
        filename: "/private/policies/leave.pdf",
        page_number: 4,
        section_title: "Eligibility",
        chunk_index: 2,
        excerpt: "Eligible employees may request leave.",
        retrieval_score: 0.7892,
      },
    ],
    llm_provider: "openai",
    model_name: "configured-model",
    fallback_used: false,
    ...overrides,
  };
}

describe("adaptAskResponse", () => {
  it("normalizes a supported answer and removes filename paths", () => {
    const result = adaptAskResponse(supportedResponse());

    expect(result.state).toBe("completed_supported");
    expect(result.citations[0]?.document).toBe("leave.pdf");
    expect(result.citations[0]?.retrievalScore).toBe(0.7892);
    expect(result.confidence.reasons).toEqual([
      "Direct evidence supports the requested policy detail.",
    ]);
  });

  it("classifies an unsupported backend decision without parsing answer text", () => {
    const result = adaptAskResponse(
      supportedResponse({
        answer: "Any arbitrary fallback wording.",
        answer_ready: false,
        evidence_status: "insufficient",
        confidence_score: 0.2,
        citation_count: 0,
        citations: [],
        llm_provider: "none",
        model_name: null,
        fallback_used: true,
      }),
    );

    expect(result.state).toBe("completed_unsupported");
    expect(result.citations).toHaveLength(0);
  });

  it("classifies provider fallback structurally", () => {
    const result = adaptAskResponse(
      supportedResponse({ fallback_used: true, llm_provider: "citation-only" }),
    );

    expect(result.state).toBe("completed_provider_fallback");
    expect(result.citations).toHaveLength(1);
  });

  it("accepts an older supported response without fallback_used", () => {
    const response = supportedResponse() as unknown as Record<string, unknown>;
    delete response.fallback_used;

    expect(adaptAskResponse(response).state).toBe("completed_supported");
  });

  it("accepts a missing optional confidence breakdown", () => {
    const result = adaptAskResponse(
      supportedResponse({ confidence_breakdown: null }),
    );

    expect(result.state).toBe("completed_supported");
    expect(result.confidence.reasons).toEqual([]);
  });

  it.each([
    ["strong", "High evidence confidence"],
    ["moderate", "Moderate evidence confidence"],
    ["weak", "Low evidence confidence"],
    ["insufficient", "Insufficient evidence"],
    ["unrecognized", "Confidence assessed"],
  ])("maps %s confidence to a plain-language label", (status, label) => {
    expect(
      adaptAskResponse(supportedResponse({ evidence_status: status })).confidence.label,
    ).toBe(label);
  });

  it("normalizes a missing citation section and preserves a long display excerpt", () => {
    const excerpt = "Policy evidence. ".repeat(60);
    const response = supportedResponse();
    response.citations[0] = {
      ...response.citations[0]!,
      section_title: null,
      excerpt,
    };
    const citation = adaptAskResponse(response).citations[0];

    expect(citation?.section).toBe("Policy excerpt");
    expect(citation?.excerpt).toBe(excerpt.trim());
  });

  it("removes Windows-style paths and control characters from filenames", () => {
    const response = supportedResponse();
    response.citations[0] = {
      ...response.citations[0]!,
      filename: "C:\\private\\employee\u0000-policy.pdf",
    };

    expect(adaptAskResponse(response).citations[0]?.document).toBe(
      "employee-policy.pdf",
    );
  });

  it("rejects a supported response without citations", () => {
    const result = adaptAskResponse(
      supportedResponse({ citation_count: 0, citations: [] }),
    );

    expect(result.state).toBe("invalid_response");
  });

  it("rejects malformed upstream data", () => {
    expect(adaptAskResponse({ success: true, answer_ready: true }).state).toBe(
      "invalid_response",
    );
  });

  it("rejects a citation missing its required retrieval score", () => {
    const response = supportedResponse() as unknown as Record<string, unknown>;
    const citations = response.citations as Array<Record<string, unknown>>;
    delete citations[0]?.retrieval_score;

    expect(adaptAskResponse(response).state).toBe("invalid_response");
  });
});
