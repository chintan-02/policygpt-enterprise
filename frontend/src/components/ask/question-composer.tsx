import { Search, Square } from "lucide-react";
import type { FormEvent, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { MAX_QUESTION_LENGTH } from "@/lib/validation/ask";

export function QuestionComposer({
  question,
  onQuestionChange,
  onSubmit,
  onCancel,
  disabled,
  pending,
  validationMessage,
  autoFocus = false,
}: {
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  disabled: boolean;
  pending: boolean;
  validationMessage?: string | null;
  autoFocus?: boolean;
}) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-neutral-200 bg-white p-5">
      <label htmlFor="policy-question" className="text-sm font-semibold text-neutral-800">
        Policy question
      </label>
      <div id="question-scope" className="mt-2 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold tracking-[0.08em] text-neutral-600 uppercase">
          Search scope
        </span>
        <span className="rounded-full border border-teal-100 bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-800">
          All indexed documents
        </span>
      </div>
      <textarea
        id="policy-question"
        value={question}
        onChange={(event) => onQuestionChange(event.target.value)}
        onKeyDown={handleKeyDown}
        maxLength={MAX_QUESTION_LENGTH}
        rows={5}
        autoFocus={autoFocus}
        disabled={disabled || pending}
        aria-invalid={Boolean(validationMessage)}
        aria-describedby={validationMessage ? "question-scope question-error" : "question-scope"}
        placeholder="Ask about an HR policy, SOP, workplace rule, leave entitlement, information security requirement, or compliance procedure."
        className="mt-4 min-h-32 w-full resize-y rounded-lg border border-neutral-300 bg-white px-3.5 py-3 text-sm leading-6 text-neutral-900 outline-none placeholder:text-neutral-400 focus:border-teal-700 focus:ring-3 focus:ring-teal-700/15 disabled:cursor-not-allowed disabled:bg-neutral-50 disabled:text-neutral-500"
      />
      <div className="mt-2 flex items-start justify-between gap-3">
        <div>
          {validationMessage ? (
            <p id="question-error" className="text-xs font-medium text-error-700">
              {validationMessage}
            </p>
          ) : (
            <p className="text-xs text-neutral-500">Press ⌘/Ctrl + Enter to ask.</p>
          )}
        </div>
        <div className="font-metric text-xs text-neutral-500" aria-live="polite">
          {question.length.toLocaleString()} / {MAX_QUESTION_LENGTH.toLocaleString()}
        </div>
      </div>
      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <Button className="w-full sm:w-auto" type="submit" size="lg" disabled={disabled || pending || !question.trim()}>
          <Search aria-hidden="true" />
          Find evidence-backed answer
        </Button>
        {pending ? (
          <Button className="w-full sm:w-auto" type="button" variant="outline" size="lg" onClick={onCancel}>
            <Square aria-hidden="true" />
            Cancel
          </Button>
        ) : null}
      </div>
    </form>
  );
}
