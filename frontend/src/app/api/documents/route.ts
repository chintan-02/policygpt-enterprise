import { getDocuments, mapDocumentFetchError } from "@/lib/api/documents";
import { DOCUMENT_PAGE_SIZE, parseDocumentQuery } from "@/lib/domain/document";

function errorResponse(error: ReturnType<typeof mapDocumentFetchError>) {
  return Response.json(
    { error: { code: error.code, message: error.message } },
    { status: error.status, headers: { "Cache-Control": "no-store" } },
  );
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const query = parseDocumentQuery(url.searchParams);
  const requestedLimit = Number(url.searchParams.get("limit") ?? DOCUMENT_PAGE_SIZE);
  const limit = Number.isInteger(requestedLimit) && requestedLimit >= 1 && requestedLimit <= 100
    ? requestedLimit
    : DOCUMENT_PAGE_SIZE;
  try {
    const data = await getDocuments(query, request.signal, limit);
    return Response.json(data, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return errorResponse(mapDocumentFetchError(error));
  }
}
