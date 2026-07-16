import { ListChecks } from "lucide-react";
import { PlaceholderPage } from "@/components/policygpt/placeholder-page";

export default function EvaluationCasesPage() {
  return (
    <PlaceholderPage
      title="Evaluation cases"
      description="Inspect question-level evidence, answers, citations, and safety outcomes."
      emptyTitle="No evaluation cases available"
      emptyDescription="Case-level results will appear after persisted evaluation data is connected."
      icon={ListChecks}
    />
  );
}
