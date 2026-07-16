import { AskWorkspace } from "@/components/ask/ask-workspace";
import { PageHeader } from "@/components/system/page-header";
import { getBackendHealth } from "@/lib/api/health";

export default async function AskPage() {
  const health = await getBackendHealth();

  return (
    <>
      <PageHeader
        title="Ask PolicyGPT"
        description="Ask an enterprise policy question and verify the response against source evidence."
      />
      <AskWorkspace health={health} />
    </>
  );
}
