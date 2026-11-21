import { AskWorkspace } from "@/components/ask/ask-workspace";
import { PageHeader } from "@/components/system/page-header";
import { getDocuments } from "@/lib/api/documents";
import { getBackendHealth } from "@/lib/api/health";

export default async function AskPage() {
  const [health, registry] = await Promise.all([
    getBackendHealth(),
    getDocuments({ q: "", status: "ready", offset: 0 }, undefined, 100).catch(() => null),
  ]);
  const documents = registry?.items.map(({ document_id, filename }) => ({ id: document_id, filename })) ?? [];

  return (
    <>
      <PageHeader
        title="Ask PolicyGPT"
        description="Ask an enterprise policy question and verify the response against source evidence."
      />
      <AskWorkspace health={health} documents={documents} />
    </>
  );
}
