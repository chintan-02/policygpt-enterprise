import { MessageSquareText } from "lucide-react";
import { PlaceholderPage } from "@/components/policygpt/placeholder-page";

export default function AskPage() {
  return (
    <PlaceholderPage
      title="Ask PolicyGPT"
      description="Ask an enterprise policy question and verify every claim against source evidence."
      emptyTitle="Evidence-backed question workspace"
      emptyDescription="The real FastAPI Ask workflow is connected in Phase 14B."
      icon={MessageSquareText}
    />
  );
}
