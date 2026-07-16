import type { components } from "@/lib/api/generated";
import type {
  ParsedDocumentDetail,
  ParsedDocumentList,
  ParsedDocumentStatus,
  ParsedDocumentUpload,
} from "@/lib/validation/document";

export type DocumentStatus = components["schemas"]["DocumentStatus"];
export type DocumentProcessingStage =
  components["schemas"]["DocumentProcessingStage"];
export type DocumentSummary = ParsedDocumentList["items"][number];
export type DocumentDetail = ParsedDocumentDetail;
export type DocumentStatusResult = ParsedDocumentStatus;
export type DocumentUploadResult = ParsedDocumentUpload;

export const DOCUMENT_PAGE_SIZE = 20;

export const documentStatusLabels: Record<DocumentStatus, string> = {
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

export const documentStatusTones = {
  processing: "info",
  ready: "success",
  failed: "error",
} as const satisfies Record<DocumentStatus, "info" | "success" | "error">;

export const processingStageLabels: Record<DocumentProcessingStage, string> = {
  received: "Received",
  stored: "Source stored",
  extracting: "Extracting text",
  cleaning: "Cleaning text",
  chunking: "Creating chunks",
  embedding: "Generating embeddings",
  indexing: "Indexing evidence",
  complete: "Complete",
  failed: "Failed",
};

export const lifecycleStages = [
  "received",
  "stored",
  "extracting",
  "cleaning",
  "chunking",
  "embedding",
  "indexing",
  "complete",
] as const satisfies readonly DocumentProcessingStage[];

export type LifecycleStepState = "complete" | "active" | "pending" | "failed";
export type LifecycleStep = {
  stage: (typeof lifecycleStages)[number];
  label: string;
  state: LifecycleStepState;
};

const failureStageByCode: Record<string, (typeof lifecycleStages)[number]> = {
  storage_failed: "stored",
  extraction_failed: "extracting",
  cleaning_failed: "cleaning",
  chunking_failed: "chunking",
  embedding_failed: "embedding",
  indexing_failed: "indexing",
  metadata_update_failed: "complete",
};

export const safeErrorCodeLabels: Record<string, string> = {
  storage_failed: "Source storage",
  extraction_failed: "Text extraction",
  cleaning_failed: "Text cleaning",
  chunking_failed: "Chunk creation",
  embedding_failed: "Embedding generation",
  indexing_failed: "Evidence indexing",
  metadata_update_failed: "Metadata persistence",
};

export function lifecyclePresentation(input: {
  status: DocumentStatus;
  processing_stage: DocumentProcessingStage;
  error_code?: string | null;
}): LifecycleStep[] {
  if (input.status === "ready" && input.processing_stage === "complete") {
    return lifecycleStages.map((stage) => ({
      stage,
      label: processingStageLabels[stage],
      state: "complete",
    }));
  }

  if (input.status === "failed") {
    const failedStage = input.error_code
      ? failureStageByCode[input.error_code]
      : undefined;
    const failedIndex = failedStage ? lifecycleStages.indexOf(failedStage) : -1;
    return lifecycleStages.map((stage, index) => ({
      stage,
      label: processingStageLabels[stage],
      state:
        failedIndex < 0
          ? "pending"
          : index < failedIndex
            ? "complete"
            : index === failedIndex
              ? "failed"
              : "pending",
    }));
  }

  const activeIndex = lifecycleStages.indexOf(
    input.processing_stage as (typeof lifecycleStages)[number],
  );
  return lifecycleStages.map((stage, index) => ({
    stage,
    label: processingStageLabels[stage],
    state:
      activeIndex < 0
        ? "pending"
        : index < activeIndex
          ? "complete"
          : index === activeIndex
            ? "active"
            : "pending",
  }));
}

export type DocumentQuery = {
  q: string;
  status?: DocumentStatus;
  offset: number;
};

type SearchInput = Record<string, string | string[] | undefined> | URLSearchParams;

function firstValue(input: SearchInput, key: string): string | undefined {
  const value = input instanceof URLSearchParams ? input.get(key) ?? undefined : input[key];
  return Array.isArray(value) ? value[0] : value;
}

export function parseDocumentQuery(input: SearchInput): DocumentQuery {
  const q = (firstValue(input, "q") ?? "").trim();
  const rawStatus = firstValue(input, "status");
  const status = (["ready", "processing", "failed"] as const).find(
    (value) => value === rawStatus,
  );
  const rawOffset = firstValue(input, "offset") ?? "0";
  const parsedOffset = /^\d+$/.test(rawOffset) ? Number(rawOffset) : 0;
  return {
    q,
    status,
    offset: Number.isSafeInteger(parsedOffset) && parsedOffset >= 0 ? parsedOffset : 0,
  };
}

export function documentQueryString(query: DocumentQuery): string {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.status) params.set("status", query.status);
  if (query.offset > 0) params.set("offset", String(query.offset));
  return params.toString();
}

export function updateDocumentQuery(
  current: DocumentQuery,
  change: Partial<Pick<DocumentQuery, "q" | "status" | "offset">>,
  resetOffset = false,
): DocumentQuery {
  return {
    ...current,
    ...change,
    q: (change.q ?? current.q).trim(),
    offset: resetOffset ? 0 : Math.max(0, change.offset ?? current.offset),
  };
}

export function documentResultRange(list: ParsedDocumentList): string {
  if (list.total === 0) return "Showing 0 of 0";
  if (list.items.length === 0) return `Showing 0 of ${list.total}`;
  return `Showing ${list.offset + 1}–${list.offset + list.items.length} of ${list.total}`;
}

export function nextDocumentOffset(list: ParsedDocumentList): number | null {
  return list.offset + list.items.length >= list.total
    ? null
    : list.offset + list.limit;
}

export function previousDocumentOffset(list: ParsedDocumentList): number | null {
  return list.offset === 0 ? null : Math.max(0, list.offset - list.limit);
}

export function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    value,
  );
}

export function isPdfFileCandidate(name: string, contentType: string): boolean {
  return name.trim().toLowerCase().endsWith(".pdf") &&
    (!contentType || contentType.toLowerCase() === "application/pdf");
}

export type UploadErrorPresentation = {
  title: string;
  message: string;
  tone: "error" | "warning" | "info";
};

export function uploadErrorPresentation(code: string): UploadErrorPresentation {
  const normalized = code.toLowerCase();
  if (normalized === "database_unavailable") {
    return {
      title: "Document metadata is unavailable",
      message:
        "PolicyGPT could not access the persistent metadata service. The PDF was not indexed.",
      tone: "info",
    };
  }
  if (normalized === "backend_unavailable") {
    return { title: "Document service is unavailable", message: "PolicyGPT could not reach the backend service. Check the local services and try again.", tone: "info" };
  }
  if (normalized === "request_timeout") {
    return { title: "Document processing timed out", message: "The request did not finish in time. Confirm the service state before trying again.", tone: "warning" };
  }
  if (normalized === "extraction_failed") {
    return { title: "Text extraction failed", message: "PolicyGPT could not extract usable text from this PDF.", tone: "error" };
  }
  if (normalized === "cleaning_failed") {
    return { title: "Document processing failed", message: "PolicyGPT could not prepare the extracted text for indexing.", tone: "error" };
  }
  if (normalized === "chunking_failed") {
    return { title: "Chunk creation failed", message: "PolicyGPT could not create searchable policy sections from the PDF.", tone: "error" };
  }
  if (normalized === "embedding_failed") {
    return { title: "Embedding generation failed", message: "PolicyGPT could not generate retrieval representations for this document.", tone: "error" };
  }
  if (normalized === "indexing_failed") {
    return { title: "Evidence indexing failed", message: "The document record was created, but searchable evidence indexing did not complete.", tone: "error" };
  }
  if (normalized === "bad_request" || normalized === "unsupported_file_type") {
    return { title: "Only PDF files are supported", message: "Select a valid PDF document and try again.", tone: "warning" };
  }
  if (normalized === "file_too_large") {
    return { title: "PDF exceeds the upload limit", message: "Select a smaller policy PDF that fits the configured server limit.", tone: "warning" };
  }
  return { title: "The policy could not be processed", message: "Try again or review the backend logs for technical details.", tone: "error" };
}
