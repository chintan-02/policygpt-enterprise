import { Scale } from "lucide-react";
import { PlaceholderPage } from "@/components/policygpt/placeholder-page";

export default function EvaluationConfidencePage() {
  return (
    <PlaceholderPage
      title="Confidence calibration"
      description="Compare calibrated evidence confidence with observed answer quality."
      emptyTitle="Confidence results are not connected"
      emptyDescription="Calibration views will be available after evaluation persistence is enabled."
      icon={Scale}
    />
  );
}
