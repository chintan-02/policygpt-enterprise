import { DocumentsProduct } from "@/components/features/documents/documents-product";
import { loadDocumentsPageState } from "@/lib/api/documents";
import { documentQueryString, parseDocumentQuery } from "@/lib/domain/document";

export default async function DocumentsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = parseDocumentQuery(await searchParams);
  const state = await loadDocumentsPageState(query);
  return <DocumentsProduct key={documentQueryString(query)} initialState={state} query={query} />;
}
