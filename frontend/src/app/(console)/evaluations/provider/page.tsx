import { ServerCog } from "lucide-react";
import { PlaceholderPage } from "@/components/policygpt/placeholder-page";

export default function EvaluationProviderPage() {
  return (
    <PlaceholderPage
      title="Provider reliability"
      description="Review provider outcomes, retries, safe fallbacks, and latency."
      emptyTitle="Provider evaluation is not measured"
      emptyDescription="Reliability results will appear only after real evaluation runs are connected."
      icon={ServerCog}
    />
  );
}
