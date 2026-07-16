"use client";

import {
  createContext,
  type Dispatch,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useReducer,
  useRef,
} from "react";
import { askPolicyQuestion, AskApiError } from "@/lib/api/ask";
import type { AskResult } from "@/lib/domain/ask";
import {
  type AskWorkspaceAction,
  type AskWorkspaceSnapshot,
  askWorkspaceReducer,
  initialAskWorkspaceSnapshot,
} from "@/lib/domain/ask-workspace";
import { askRequestSchema } from "@/lib/validation/ask";

type AskWorkspaceContextValue = AskWorkspaceSnapshot & {
  isPending: boolean;
  setQuestion: (question: string) => void;
  setEditingQuestion: (editing: boolean) => void;
  submit: (question: string) => Promise<AskResult | null>;
  cancel: () => void;
  reset: () => void;
};

const AskWorkspaceContext = createContext<AskWorkspaceContextValue | null>(null);

function dispatchFailure(
  dispatch: Dispatch<AskWorkspaceAction>,
  error: unknown,
) {
  if (error instanceof AskApiError) {
    dispatch({
      type: "request_failed",
      state: error.code === "invalid_response" ? "invalid_response" : "request_failed",
      message: error.message,
    });
    return;
  }

  dispatch({
    type: "request_failed",
    state: "request_failed",
    message: "PolicyGPT could not complete the request. Try again.",
  });
}

export function AskWorkspaceProvider({ children }: { children: ReactNode }) {
  const [snapshot, dispatch] = useReducer(
    askWorkspaceReducer,
    initialAskWorkspaceSnapshot,
  );
  const controllerRef = useRef<AbortController | null>(null);

  const setQuestion = useCallback((question: string) => {
    dispatch({ type: "set_question", question });
  }, []);

  const setEditingQuestion = useCallback((editing: boolean) => {
    dispatch({ type: "set_editing", editing });
  }, []);

  const submit = useCallback(async (question: string) => {
    if (controllerRef.current) return null;

    dispatch({ type: "validation_started" });
    const parsed = askRequestSchema.safeParse({ question });

    if (!parsed.success) {
      dispatch({
        type: "validation_failed",
        message:
          parsed.error.issues[0]?.message ?? "Enter a valid policy question.",
      });
      return null;
    }

    const controller = new AbortController();
    controllerRef.current = controller;
    dispatch({ type: "retrieval_started" });

    try {
      const result = await askPolicyQuestion(parsed.data, controller.signal);
      dispatch({ type: "completed", result });
      return result;
    } catch (error) {
      if (controller.signal.aborted) {
        dispatch({
          type: "cancelled",
          message: "The request was cancelled. Your question is still available.",
        });
      } else {
        dispatchFailure(dispatch, error);
      }
    } finally {
      controllerRef.current = null;
    }

    return null;
  }, []);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    dispatch({ type: "reset" });
  }, []);

  const value = useMemo<AskWorkspaceContextValue>(
    () => ({
      ...snapshot,
      isPending:
        snapshot.state === "validating" || snapshot.state === "retrieving",
      setQuestion,
      setEditingQuestion,
      submit,
      cancel,
      reset,
    }),
    [snapshot, setQuestion, setEditingQuestion, submit, cancel, reset],
  );

  return (
    <AskWorkspaceContext.Provider value={value}>
      {children}
    </AskWorkspaceContext.Provider>
  );
}

export function useAskWorkspaceContext() {
  const context = useContext(AskWorkspaceContext);
  if (!context) {
    throw new Error("useAsk must be used within AskWorkspaceProvider.");
  }
  return context;
}
