import { Pencil, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

export function QuestionSummary({
  question,
  onEdit,
  onAskAnother,
}: {
  question: string;
  onEdit: () => void;
  onAskAnother: () => void;
}) {
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-neutral-200 bg-white px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <div className="text-xs font-semibold tracking-[0.08em] text-neutral-500 uppercase">
          Question
        </div>
        <p className="mt-1 break-words text-sm leading-6 font-medium text-neutral-800">
          {question}
        </p>
      </div>
      <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
        <Button
          type="button"
          variant="outline"
          size="sm"
          aria-label="Edit the submitted policy question"
          onClick={onEdit}
        >
          <Pencil aria-hidden="true" />
          Edit question
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          aria-label="Clear this result and ask another policy question"
          onClick={onAskAnother}
        >
          <Plus aria-hidden="true" />
          Ask another question
        </Button>
      </div>
    </section>
  );
}
