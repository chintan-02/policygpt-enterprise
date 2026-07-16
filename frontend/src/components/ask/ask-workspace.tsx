"use client";

import { RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAsk } from "@/hooks/use-ask";
import type { FrontendHealthResponse } from "@/lib/api/types";
import {
  composerPresentation,
  evidencePanelResetState,
  isCompletedResultState,
  questionAction,
  resultPresentation,
} from "@/lib/domain/ask-presentation";
import { AnswerPanel } from "./answer-panel";
import { AnswerStatusBanner } from "./answer-status-banner";
import { EvidencePanel } from "./evidence-panel";
import { QuestionComposer } from "./question-composer";
import { QuestionSummary } from "./question-summary";
import { UnsupportedResult } from "./unsupported-result";

const messageFocusStates = new Set([
  "invalid_response",
  "request_failed",
  "cancelled",
]);

function LoadingPanel() {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-5" aria-label="Retrieving policy evidence">
      <Skeleton className="h-5 w-40" />
      <Skeleton className="mt-4 h-4 w-full" />
      <Skeleton className="mt-3 h-4 w-11/12" />
      <Skeleton className="mt-3 h-4 w-4/5" />
      <div className="mt-5 text-sm font-medium text-neutral-600" role="status">
        Retrieving and validating policy evidence
      </div>
    </div>
  );
}

export function AskWorkspace({ health }: { health: FrontendHealthResponse }) {
  const [question, setQuestion] = useState("");
  const [editingQuestion, setEditingQuestion] = useState(true);
  const {
    state,
    result,
    message,
    isPending,
    requestSequence,
    submit,
    cancel,
    reset,
  } = useAsk();
  const resultFocusRef = useRef<HTMLElement>(null);
  const messageFocusRef = useRef<HTMLDivElement>(null);
  const unavailable = !health.backendReachable;
  const composerMode = composerPresentation(state, editingQuestion);
  const presentation = resultPresentation(state);
  const evidenceReset = evidencePanelResetState(requestSequence);

  useEffect(() => {
    if (isCompletedResultState(state)) {
      resultFocusRef.current?.focus();
    } else if (messageFocusStates.has(state)) {
      messageFocusRef.current?.focus();
    }
  }, [state]);

  const validationMessage = state === "validation_error" ? message : null;

  function editQuestion() {
    if (!result) return;
    const next = questionAction("edit", result.question);
    setQuestion(next.question);
    setEditingQuestion(next.editing);
  }

  function askAnotherQuestion() {
    const next = questionAction("ask_another", result?.question ?? question);
    if (next.resetResult) reset();
    setQuestion(next.question);
    setEditingQuestion(next.editing);
  }

  async function submitQuestion() {
    setEditingQuestion(true);
    const nextResult = await submit(question);
    if (nextResult && isCompletedResultState(nextResult.state)) {
      setEditingQuestion(false);
    }
  }

  return (
    <div className="space-y-4">
      {unavailable ? (
        <AnswerStatusBanner variant="warning" title="Ask is unavailable">
          <div className="flex flex-wrap items-center gap-3">
            <span>{health.message} Start the FastAPI service, then refresh.</span>
            <Button type="button" variant="outline" size="sm" onClick={() => window.location.reload()}>
              <RotateCcw aria-hidden="true" />
              Refresh
            </Button>
          </div>
        </AnswerStatusBanner>
      ) : null}

      {composerMode === "summary" && result ? (
        <QuestionSummary
          question={result.question}
          onEdit={editQuestion}
          onAskAnother={askAnotherQuestion}
        />
      ) : (
        <QuestionComposer
          question={question}
          onQuestionChange={setQuestion}
          onSubmit={submitQuestion}
          onCancel={cancel}
          disabled={unavailable}
          pending={isPending}
          validationMessage={validationMessage}
          autoFocus={isCompletedResultState(state) && editingQuestion}
        />
      )}

      {presentation.layout === "two_column" && result ? (
        <div className="grid min-w-0 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
          <AnswerPanel
            key={`answer-request-${requestSequence}`}
            result={result}
            variant={presentation.kind === "provider_fallback" ? "provider_fallback" : "supported"}
            focusRef={resultFocusRef}
          />
          <EvidencePanel
            key={evidenceReset.key}
            result={result}
            requestSequence={requestSequence}
          />
        </div>
      ) : null}

      {presentation.layout === "full_width" && result ? (
        <UnsupportedResult
          key={`unsupported-request-${requestSequence}`}
          result={result}
          focusRef={resultFocusRef}
        />
      ) : null}

      {presentation.layout === "none" ? (
        <div className="grid min-w-0 items-start gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(340px,2fr)]">
          <div className="space-y-4">
            {isPending ? <LoadingPanel /> : null}

            {state === "idle" || state === "validation_error" ? (
              <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-6">
                <h2 className="text-base font-semibold text-neutral-900">Ready for a policy question</h2>
                <p className="mt-2 max-w-xl text-sm leading-6 text-neutral-600">
                  PolicyGPT answers only when retrieved policy evidence passes the backend confidence and safety checks.
                </p>
              </div>
            ) : null}

            {state === "request_failed" ? (
              <AnswerStatusBanner
                focusRef={messageFocusRef}
                variant="error"
                title="Request could not be completed"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <span>{message}</span>
                  <Button type="button" variant="outline" size="sm" onClick={submitQuestion}>
                    Try again
                  </Button>
                </div>
              </AnswerStatusBanner>
            ) : null}

            {state === "invalid_response" ? (
              <AnswerStatusBanner
                focusRef={messageFocusRef}
                variant="error"
                title="Response could not be verified"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <span>{message ?? "The backend response could not be safely presented."}</span>
                  <Button type="button" variant="outline" size="sm" onClick={submitQuestion}>
                    Try again
                  </Button>
                </div>
              </AnswerStatusBanner>
            ) : null}

            {state === "cancelled" ? (
              <AnswerStatusBanner
                focusRef={messageFocusRef}
                variant="neutral"
                title="Request cancelled"
              >
                {message}
              </AnswerStatusBanner>
            ) : null}
          </div>

          {isPending ? (
            <LoadingPanel />
          ) : (
            <EvidencePanel
              key={evidenceReset.key}
              result={null}
              requestSequence={requestSequence}
            />
          )}
        </div>
      ) : null}
    </div>
  );
}
