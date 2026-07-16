import { getDocument, mapDocumentFetchError } from "@/lib/api/documents";
import { isUuid } from "@/lib/domain/document";

type RouteContext = { params: Promise<{ documentId: string }> };

export async function GET(request: Request, context: RouteContext) {
  const { documentId } = await context.params;
  if (!isUuid(documentId)) {
    return Response.json(
      { error: { code: "DOCUMENT_NOT_FOUND", message: "Document metadata was not found." } },
      { status: 404, headers: { "Cache-Control": "no-store" } },
    );
  }
  try {
    return Response.json(await getDocument(documentId, request.signal), {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    const safe = mapDocumentFetchError(error);
    return Response.json(
      { error: { code: safe.code, message: safe.message } },
      { status: safe.status, headers: { "Cache-Control": "no-store" } },
    );
  }
}
