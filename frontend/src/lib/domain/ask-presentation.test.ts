import { describe, expect, it } from "vitest";
import {
  composerPresentation,
  evidencePanelResetState,
  ENGINEERING_DETAILS_DEFAULT_OPEN,
  expandedCitationForRequest,
  nextExpandedCitation,
  questionAction,
  resultPresentation,
  selectCitationForRequest,
} from "./ask-presentation";

describe("Ask compact-result presentation", () => {
  it.each([
    "completed_supported",
    "completed_unsupported",
    "completed_provider_fallback",
  ] as const)("collapses the composer after %s", (state) => {
    expect(composerPresentation(state, false)).toBe("summary");
  });

  it("restores the existing question for editing", () => {
    expect(questionAction("edit", "What is the leave policy?")).toEqual({
      question: "What is the leave policy?",
      editing: true,
      resetResult: false,
    });
    expect(composerPresentation("completed_supported", true)).toBe("composer");
  });

  it("clears the question and result for another question", () => {
    expect(questionAction("ask_another", "Prior question")).toEqual({
      question: "",
      editing: true,
      resetResult: true,
    });
  });

  it("uses the compact two-column supported result", () => {
    expect(resultPresentation("completed_supported")).toEqual({
      layout: "two_column",
      kind: "supported",
      showEvidence: true,
    });
  });

  it("uses a full-width unsupported result without evidence", () => {
    expect(resultPresentation("completed_unsupported")).toEqual({
      layout: "full_width",
      kind: "unsupported",
      showEvidence: false,
    });
  });

  it("keeps provider fallback in the evidence layout", () => {
    expect(resultPresentation("completed_provider_fallback")).toEqual({
      layout: "two_column",
      kind: "provider_fallback",
      showEvidence: true,
    });
  });

  it("keeps engineering details collapsed by default", () => {
    expect(ENGINEERING_DETAILS_DEFAULT_OPEN).toBe(false);
  });

  it("allows only one citation excerpt to be expanded", () => {
    expect(nextExpandedCitation(null, "source-1")).toBe("source-1");
    expect(nextExpandedCitation("source-1", "source-2")).toBe("source-2");
    expect(nextExpandedCitation("source-2", "source-2")).toBeNull();
  });

  it("collapses Source 3 when a new request starts", () => {
    const sourceThreeExpanded = selectCitationForRequest(
      { requestSequence: 7, expandedCitationId: null },
      7,
      "source-3",
    );

    expect(sourceThreeExpanded.expandedCitationId).toBe("source-3");
    expect(expandedCitationForRequest(sourceThreeExpanded, 8)).toBeNull();
    expect(evidencePanelResetState(8).expandedCitationId).toBeNull();
  });

  it("resets evidence scroll position to the top for a new request", () => {
    const previousScrollTop = 640;
    const reset = evidencePanelResetState(12);

    expect(previousScrollTop).toBeGreaterThan(0);
    expect(reset.scrollTop).toBe(0);
  });

  it("uses a new reset identity when the same question is submitted twice", () => {
    const firstRequest = evidencePanelResetState(20);
    const repeatedRequest = evidencePanelResetState(21);

    expect(firstRequest.key).not.toBe(repeatedRequest.key);
    expect(repeatedRequest.expandedCitationId).toBeNull();
    expect(repeatedRequest.scrollTop).toBe(0);
  });
});
