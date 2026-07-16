import { mapDocumentStatus } from "@/lib/api/documents";
import { getFastApiUrl, ServerEnvironmentError } from "@/lib/environment";
import { backendErrorSchema, documentUploadSchema } from "@/lib/validation/document";

const UPLOAD_TIMEOUT_MS = 120_000;

function errorResponse(code: string, message: string, status: number) {
  return Response.json(
    { error: { code, message } },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

function normalizeUploadErrorCode(code: string, message: string): string {
  const normalizedCode = code.toLowerCase();
  const normalizedMessage = message.toLowerCase();
  if (normalizedCode === "bad_request") {
    if (normalizedMessage.includes("too large")) return "FILE_TOO_LARGE";
    if (normalizedMessage.includes("only pdf") || normalizedMessage.includes("content type")) return "UNSUPPORTED_FILE_TYPE";
    if (normalizedMessage.includes("extract") || normalizedMessage.includes("opened as a valid pdf")) return "EXTRACTION_FAILED";
  }
  if (normalizedMessage.includes("index")) return "INDEXING_FAILED";
  if (normalizedMessage.includes("embed")) return "EMBEDDING_FAILED";
  if (normalizedMessage.includes("chunk")) return "CHUNKING_FAILED";
  return code;
}

export async function POST(request: Request) {
  const contentType = request.headers.get("content-type")?.toLowerCase() ?? "";
  if (!contentType.startsWith("multipart/form-data")) {
    return errorResponse("VALIDATION_ERROR", "Select one PDF document to upload.", 415);
  }
  const incoming = await request.formData().catch(() => null);
  const file = incoming?.get("file");
  if (!(file instanceof File) || !file.name.toLowerCase().endsWith(".pdf")) {
    return errorResponse("UNSUPPORTED_FILE_TYPE", "Only PDF files are supported.", 400);
  }
  const upstream = new FormData();
  upstream.set("file", file, file.name);
  try {
    const response = await fetch(`${getFastApiUrl()}/api/v1/documents/upload`, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: upstream,
      cache: "no-store",
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(UPLOAD_TIMEOUT_MS)]),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const parsedError = backendErrorSchema.safeParse(payload);
      const mapped = mapDocumentStatus(response.status);
      const code = parsedError.success
        ? normalizeUploadErrorCode(parsedError.data.error.code, parsedError.data.error.message)
        : mapped.code;
      const message = parsedError.success ? parsedError.data.error.message : mapped.message;
      return errorResponse(code, message, mapped.status);
    }
    const parsed = documentUploadSchema.safeParse(payload);
    if (!parsed.success) {
      return errorResponse("INVALID_RESPONSE", "The document service returned an invalid upload response.", 502);
    }
    return Response.json(parsed.data, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    if (error instanceof ServerEnvironmentError || error instanceof TypeError) {
      return errorResponse("BACKEND_UNAVAILABLE", "The document service could not be reached.", 502);
    }
    if (error instanceof DOMException && error.name === "TimeoutError") {
      return errorResponse("REQUEST_TIMEOUT", "The document upload timed out. Try again.", 504);
    }
    if (request.signal.aborted) return errorResponse("REQUEST_FAILED", "The upload was cancelled.", 499);
    return errorResponse("REQUEST_FAILED", "The policy could not be processed.", 500);
  }
}
