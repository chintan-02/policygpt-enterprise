import "server-only";

import { fetchFromBackend } from "@/lib/api/client";
import type { DocumentQuery } from "@/lib/domain/document";
import { DOCUMENT_PAGE_SIZE } from "@/lib/domain/document";
import { ServerEnvironmentError } from "@/lib/environment";
import {
  documentDetailSchema,
  documentListSchema,
  documentStatusSchema,
  type ParsedDocumentDetail,
  type ParsedDocumentList,
  type ParsedDocumentStatus,
} from "@/lib/validation/document";

const DOCUMENT_TIMEOUT_MS = 10_000;

export type DocumentApiErrorCode =
  | "DOCUMENT_NOT_FOUND"
  | "DATABASE_UNAVAILABLE"
  | "BACKEND_UNAVAILABLE"
  | "REQUEST_TIMEOUT"
  | "INVALID_RESPONSE"
  | "VALIDATION_ERROR";

export class DocumentApiError extends Error {
  constructor(
    public readonly code: DocumentApiErrorCode,
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "DocumentApiError";
  }
}

export function mapDocumentStatus(status: number): DocumentApiError {
  if (status === 404) {
    return new DocumentApiError("DOCUMENT_NOT_FOUND", "Document metadata was not found.", 404);
  }
  if (status === 503) {
    return new DocumentApiError(
      "DATABASE_UNAVAILABLE",
      "Document metadata is temporarily unavailable.",
      503,
    );
  }
  if (status === 400 || status === 413 || status === 415 || status === 422) {
    return new DocumentApiError("VALIDATION_ERROR", "The document request was rejected.", status);
  }
  return new DocumentApiError("BACKEND_UNAVAILABLE", "The document service is unavailable.", 502);
}

export function mapDocumentFetchError(error: unknown): DocumentApiError {
  if (error instanceof DocumentApiError) return error;
  if (error instanceof DOMException && error.name === "TimeoutError") {
    return new DocumentApiError("REQUEST_TIMEOUT", "The document request timed out.", 504);
  }
  if (error instanceof ServerEnvironmentError || error instanceof TypeError) {
    return new DocumentApiError("BACKEND_UNAVAILABLE", "The document service is unavailable.", 502);
  }
  return new DocumentApiError("INVALID_RESPONSE", "The document service returned an invalid response.", 502);
}

function documentListPath(query: DocumentQuery, limit = DOCUMENT_PAGE_SIZE): string {
  const params = new URLSearchParams({ limit: String(limit), offset: String(query.offset) });
  if (query.q) params.set("filename", query.q);
  if (query.status) params.set("status", query.status);
  return `/api/v1/documents?${params.toString()}`;
}

export async function getDocuments(
  query: DocumentQuery,
  signal?: AbortSignal,
  limit = DOCUMENT_PAGE_SIZE,
): Promise<ParsedDocumentList> {
  try {
    const response = await fetchFromBackend(documentListPath(query, limit), {
      timeoutMs: DOCUMENT_TIMEOUT_MS,
      signal,
    });
    if (!response.ok) throw mapDocumentStatus(response.status);
    const payload: unknown = await response.json().catch(() => null);
    const parsed = documentListSchema.safeParse(payload);
    if (!parsed.success) throw new DocumentApiError("INVALID_RESPONSE", "The document registry response was invalid.", 502);
    return parsed.data;
  } catch (error) {
    throw mapDocumentFetchError(error);
  }
}

export async function getDocument(
  documentId: string,
  signal?: AbortSignal,
): Promise<ParsedDocumentDetail> {
  try {
    const response = await fetchFromBackend(`/api/v1/documents/${encodeURIComponent(documentId)}`, {
      timeoutMs: DOCUMENT_TIMEOUT_MS,
      signal,
    });
    if (!response.ok) throw mapDocumentStatus(response.status);
    const payload: unknown = await response.json().catch(() => null);
    const parsed = documentDetailSchema.safeParse(payload);
    if (!parsed.success) throw new DocumentApiError("INVALID_RESPONSE", "The document detail response was invalid.", 502);
    return parsed.data;
  } catch (error) {
    throw mapDocumentFetchError(error);
  }
}

export async function getDocumentStatus(
  documentId: string,
  signal?: AbortSignal,
): Promise<ParsedDocumentStatus> {
  try {
    const response = await fetchFromBackend(
      `/api/v1/documents/${encodeURIComponent(documentId)}/status`,
      { timeoutMs: DOCUMENT_TIMEOUT_MS, signal },
    );
    if (!response.ok) throw mapDocumentStatus(response.status);
    const payload: unknown = await response.json().catch(() => null);
    const parsed = documentStatusSchema.safeParse(payload);
    if (!parsed.success) throw new DocumentApiError("INVALID_RESPONSE", "The document status response was invalid.", 502);
    return parsed.data;
  } catch (error) {
    throw mapDocumentFetchError(error);
  }
}

export type DocumentListPageState =
  | { state: "ready"; data: ParsedDocumentList }
  | { state: "error"; code: DocumentApiErrorCode };

export async function loadDocumentsPageState(query: DocumentQuery): Promise<DocumentListPageState> {
  try {
    return { state: "ready", data: await getDocuments(query) };
  } catch (error) {
    return { state: "error", code: mapDocumentFetchError(error).code };
  }
}

export type DocumentDetailPageState =
  | { state: "ready"; data: ParsedDocumentDetail }
  | { state: "error"; code: DocumentApiErrorCode };

export async function loadDocumentDetailState(documentId: string): Promise<DocumentDetailPageState> {
  try {
    return { state: "ready", data: await getDocument(documentId) };
  } catch (error) {
    return { state: "error", code: mapDocumentFetchError(error).code };
  }
}
