import { DocumentDetailProduct } from "@/components/features/documents/document-detail";
import { loadDocumentDetailState } from "@/lib/api/documents";
import { isUuid } from "@/lib/domain/document";

export default async function DocumentDetailPage({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  const state = isUuid(documentId)
    ? await loadDocumentDetailState(documentId)
    : { state: "error" as const, code: "DOCUMENT_NOT_FOUND" as const };
  return <DocumentDetailProduct initialState={state} documentId={documentId} />;
}
