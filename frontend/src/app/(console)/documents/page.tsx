import { FileStack } from "lucide-react";
import { PlaceholderPage } from "@/components/policygpt/placeholder-page";

export default function DocumentsPage() {
  return (
    <PlaceholderPage
      title="Documents"
      description="Manage the policy sources available to PolicyGPT."
      emptyTitle="Document workspace is being connected"
      emptyDescription="Persistent document history will be added after the PostgreSQL metadata layer."
      icon={FileStack}
    />
  );
}
