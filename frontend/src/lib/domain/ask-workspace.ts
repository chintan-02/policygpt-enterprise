import type { AskCompletionState, AskResult } from "./ask";

export type AskWorkspaceState =
  | "idle"
  | "validating"
  | "retrieving"
  | AskCompletionState
  | "validation_error"
  | "request_failed"
  | "cancelled";

export type AskWorkspaceSnapshot = {
  state: AskWorkspaceState;
  result: AskResult | null;
  message: string | null;
  requestSequence: number;
  question: string;
  editingQuestion: boolean;
};

export type AskWorkspaceAction =
  | { type: "set_question"; question: string }
  | { type: "set_editing"; editing: boolean }
  | { type: "validation_started" }
  | { type: "validation_failed"; message: string }
  | { type: "retrieval_started" }
  | { type: "completed"; result: AskResult }
  | {
      type: "request_failed";
      state: "invalid_response" | "request_failed";
      message: string;
    }
  | { type: "cancelled"; message: string }
  | { type: "reset" };

export const initialAskWorkspaceSnapshot: AskWorkspaceSnapshot = {
  state: "idle",
  result: null,
  message: null,
  requestSequence: 0,
  question: "",
  editingQuestion: true,
};

export function askWorkspaceReducer(
  snapshot: AskWorkspaceSnapshot,
  action: AskWorkspaceAction,
): AskWorkspaceSnapshot {
  switch (action.type) {
    case "set_question":
      return { ...snapshot, question: action.question };
    case "set_editing":
      return { ...snapshot, editingQuestion: action.editing };
    case "validation_started":
      return { ...snapshot, state: "validating", message: null };
    case "validation_failed":
      return {
        ...snapshot,
        state: "validation_error",
        result: null,
        message: action.message,
      };
    case "retrieval_started":
      return {
        ...snapshot,
        state: "retrieving",
        result: null,
        message: null,
        requestSequence: snapshot.requestSequence + 1,
      };
    case "completed":
      return {
        ...snapshot,
        state: action.result.state,
        result: action.result,
        message: null,
        editingQuestion: action.result.state === "invalid_response",
      };
    case "request_failed":
      return {
        ...snapshot,
        state: action.state,
        message: action.message,
      };
    case "cancelled":
      return {
        ...snapshot,
        state: "cancelled",
        message: action.message,
      };
    case "reset":
      return {
        ...initialAskWorkspaceSnapshot,
        requestSequence: snapshot.requestSequence + 1,
      };
  }
}
