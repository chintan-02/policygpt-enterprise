import { Gauge } from "lucide-react";
import { PlaceholderPage } from "@/components/policygpt/placeholder-page";

export default function EvaluationOverviewPage() {
  return (
    <PlaceholderPage
      title="Evaluation overview"
      description="Review grounded-answer quality once evaluation results are connected."
      emptyTitle="No evaluation loaded"
      emptyDescription="Run and connect a full RAG evaluation to populate quality outcomes."
      icon={Gauge}
    />
  );
}
