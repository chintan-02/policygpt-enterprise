import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { AskCompletionState, AskResult } from "./ask";
import {
  askWorkspaceReducer,
  initialAskWorkspaceSnapshot,
} from "./ask-workspace";

function resultFor(state: AskCompletionState): AskResult {
  return {
    state,
    question: "What is the parental leave policy?",
    answer:
      state === "completed_unsupported"
        ? undefined
        : "Eligible employees receive policy-backed leave.",
    citations: [
      {
        id: "leave-policy:4:1:0",
        document: "leave-policy.pdf",
        page: 4,
        section: "Parental leave",
        excerpt: "Eligible employees may request parental leave.",
        retrievalScore: 0.92,
        support: state === "completed_unsupported" ? "Insufficient" : "Strong",
      },
    ],
    confidence: {
      score: 0.88,
      status: "strong",
      label: "High evidence confidence",
      reasons: ["Direct policy support was found."],
      breakdown: {
        answerability_score: 0.9,
        top_retrieval_score: 0.92,
        average_retrieval_score: 0.86,
        retrieval_margin: 0.12,
        lexical_coverage: 0.84,
        top_chunk_lexical_coverage: 0.88,
        numeric_consistency: null,
        numeric_mismatch: false,
        scope_risk: false,
        scope_risk_reason: null,
        direct_support: true,
        query_numeric_claims: [],
        evidence_numeric_claims: [],
        missing_numeric_claims: [],
        matched_query_terms: ["parental", "leave"],
        missing_query_terms: [],
        decision_reasons: ["Direct policy support was found."],
      },
    },
    provider: state === "completed_provider_fallback" ? "citation-only" : "groq",
    model: "policy-model",
  };
}

describe("Ask workspace memory state", () => {
  it.each([
    "completed_supported",
    "completed_provider_fallback",
    "completed_unsupported",
  ] as const)("retains the complete %s result across workspace remounts", (state) => {
    const result = resultFor(state);
    const withQuestion = askWorkspaceReducer(initialAskWorkspaceSnapshot, {
      type: "set_question",
      question: result.question,
    });
    const retrieving = askWorkspaceReducer(withQuestion, {
      type: "retrieval_started",
    });
    const completed = askWorkspaceReducer(retrieving, {
      type: "completed",
      result,
    });

    // A route-level Ask component can unmount and read this same provider state later.
    expect(completed).toMatchObject({
      state,
      question: result.question,
      editingQuestion: false,
      result,
    });
    expect(completed.result?.citations).toEqual(result.citations);
    expect(completed.result?.confidence).toEqual(result.confidence);
    expect(completed.result?.provider).toBe(result.provider);
    expect(completed.result?.model).toBe(result.model);
  });

  it("clears the question and all result details only on reset", () => {
    const result = resultFor("completed_supported");
    const completed = askWorkspaceReducer(
      askWorkspaceReducer(initialAskWorkspaceSnapshot, {
        type: "retrieval_started",
      }),
      { type: "completed", result },
    );
    const reset = askWorkspaceReducer(completed, { type: "reset" });

    expect(reset).toEqual({
      ...initialAskWorkspaceSnapshot,
      requestSequence: completed.requestSequence + 1,
    });
  });

  it("uses provider memory without browser persistence storage", () => {
    const providerSource = readFileSync(
      new URL(
        "../../components/ask/ask-workspace-provider.tsx",
        import.meta.url,
      ),
      "utf8",
    );

    expect(providerSource).not.toContain("local" + "Storage");
    expect(providerSource).not.toContain("session" + "Storage");
  });
});
