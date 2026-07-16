import type { AskWorkspaceState } from "./ask-workspace";

export type CompletedResultState =
  | "completed_supported"
  | "completed_unsupported"
  | "completed_provider_fallback";

export type ResultPresentation = {
  layout: "two_column" | "full_width" | "none";
  kind: "supported" | "unsupported" | "provider_fallback" | "none";
  showEvidence: boolean;
};

export type QuestionActionResult = {
  question: string;
  editing: boolean;
  resetResult: boolean;
};

export type CitationExpansionState = {
  requestSequence: number;
  expandedCitationId: string | null;
};

export type EvidencePanelResetState = {
  key: string;
  expandedCitationId: null;
  scrollTop: 0;
};

export const ENGINEERING_DETAILS_DEFAULT_OPEN = false;

export function isCompletedResultState(
  state: AskWorkspaceState,
): state is CompletedResultState {
  return [
    "completed_supported",
    "completed_unsupported",
    "completed_provider_fallback",
  ].includes(state);
}

export function composerPresentation(
  state: AskWorkspaceState,
  editing: boolean,
): "composer" | "summary" {
  return isCompletedResultState(state) && !editing ? "summary" : "composer";
}

export function resultPresentation(state: AskWorkspaceState): ResultPresentation {
  if (state === "completed_unsupported") {
    return { layout: "full_width", kind: "unsupported", showEvidence: false };
  }
  if (state === "completed_supported") {
    return { layout: "two_column", kind: "supported", showEvidence: true };
  }
  if (state === "completed_provider_fallback") {
    return {
      layout: "two_column",
      kind: "provider_fallback",
      showEvidence: true,
    };
  }
  return { layout: "none", kind: "none", showEvidence: false };
}

export function questionAction(
  action: "edit" | "ask_another",
  submittedQuestion: string,
): QuestionActionResult {
  if (action === "ask_another") {
    return { question: "", editing: true, resetResult: true };
  }
  return { question: submittedQuestion, editing: true, resetResult: false };
}

export function nextExpandedCitation(
  currentCitationId: string | null,
  selectedCitationId: string,
): string | null {
  return currentCitationId === selectedCitationId ? null : selectedCitationId;
}

export function evidencePanelResetState(
  requestSequence: number,
): EvidencePanelResetState {
  return {
    key: `evidence-request-${requestSequence}`,
    expandedCitationId: null,
    scrollTop: 0,
  };
}

export function expandedCitationForRequest(
  state: CitationExpansionState,
  requestSequence: number,
): string | null {
  return state.requestSequence === requestSequence
    ? state.expandedCitationId
    : null;
}

export function selectCitationForRequest(
  state: CitationExpansionState,
  requestSequence: number,
  selectedCitationId: string,
): CitationExpansionState {
  const currentCitationId = expandedCitationForRequest(state, requestSequence);
  return {
    requestSequence,
    expandedCitationId: nextExpandedCitation(
      currentCitationId,
      selectedCitationId,
    ),
  };
}
