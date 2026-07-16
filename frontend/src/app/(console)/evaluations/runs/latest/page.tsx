import { History } from "lucide-react";
import { PlaceholderPage } from "@/components/policygpt/placeholder-page";

export default function LatestEvaluationRunPage() {
  return (
    <PlaceholderPage
      title="Latest evaluation run"
      description="Trace the configuration and outcomes of the most recent persisted evaluation."
      emptyTitle="No evaluation run loaded"
      emptyDescription="Run details will become available after evaluation results are persisted and connected."
      icon={History}
    />
  );
}
