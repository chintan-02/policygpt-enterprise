"use client";

import { useCallback, useRef, useState } from "react";
import { askPolicyQuestion, AskApiError } from "@/lib/api/ask";
import type { AskCompletionState, AskResult } from "@/lib/domain/ask";
import { askRequestSchema } from "@/lib/validation/ask";

export type AskWorkspaceState =
  | "idle"
  | "validating"
  | "retrieving"
  | AskCompletionState
  | "validation_error"
  | "request_failed"
  | "cancelled";

export function useAsk() {
  const [state, setState] = useState<AskWorkspaceState>("idle");
  const [result, setResult] = useState<AskResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [requestSequence, setRequestSequence] = useState(0);
  const controllerRef = useRef<AbortController | null>(null);
  const requestSequenceRef = useRef(0);

  const isPending = state === "validating" || state === "retrieving";

  const advanceRequestSequence = useCallback(() => {
    requestSequenceRef.current += 1;
    setRequestSequence(requestSequenceRef.current);
  }, []);

  const submit = useCallback(
    async (question: string) => {
      if (controllerRef.current) return;

      setState("validating");
      setMessage(null);
      const parsed = askRequestSchema.safeParse({ question });

      if (!parsed.success) {
        setResult(null);
        setMessage(parsed.error.issues[0]?.message ?? "Enter a valid policy question.");
        setState("validation_error");
        return null;
      }

      const controller = new AbortController();
      advanceRequestSequence();
      controllerRef.current = controller;
      setResult(null);
      setState("retrieving");

      try {
        const nextResult = await askPolicyQuestion(parsed.data, controller.signal);
        setResult(nextResult);
        setState(nextResult.state);
        return nextResult;
      } catch (error) {
        if (controller.signal.aborted) {
          setState("cancelled");
          setMessage("The request was cancelled. Your question is still available.");
        } else if (error instanceof AskApiError) {
          setState(
            error.code === "invalid_response" ? "invalid_response" : "request_failed",
          );
          setMessage(error.message);
        } else {
          setState("request_failed");
          setMessage("PolicyGPT could not complete the request. Try again.");
        }
      } finally {
        controllerRef.current = null;
      }

      return null;
    },
    [advanceRequestSequence],
  );

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    advanceRequestSequence();
    setState("idle");
    setResult(null);
    setMessage(null);
  }, [advanceRequestSequence]);

  return {
    state,
    result,
    message,
    isPending,
    requestSequence,
    submit,
    cancel,
    reset,
  };
}
