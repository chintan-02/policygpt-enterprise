import { describe, expect, it } from "vitest";
import {
  documentQueryString,
  documentResultRange,
  documentStatusLabels,
  documentStatusTones,
  isPdfFileCandidate,
  lifecyclePresentation,
  nextDocumentOffset,
  parseDocumentQuery,
  previousDocumentOffset,
  processingStageLabels,
  safeErrorCodeLabels,
  updateDocumentQuery,
  uploadErrorPresentation,
} from "./document";
import {
  formatDocumentFileSize,
  formatDocumentTimestamp,
  shortenDocumentId,
} from "../formatters/document";
import type { ParsedDocumentList } from "../validation/document";

const documentId = "11111111-1111-4111-8111-111111111111";

function list(overrides: Partial<ParsedDocumentList> = {}): ParsedDocumentList {
  return {
    items: [], total: 0, limit: 20, offset: 0, ...overrides,
  };
}

describe("document presentation", () => {
  it("maps statuses to labels and tones", () => {
    expect(documentStatusLabels).toEqual({ processing: "Processing", ready: "Ready", failed: "Failed" });
    expect(documentStatusTones).toEqual({ processing: "info", ready: "success", failed: "error" });
  });

  it("maps every processing stage to a human label", () => {
    expect(processingStageLabels.extracting).toBe("Extracting text");
    expect(processingStageLabels.embedding).toBe("Generating embeddings");
    expect(processingStageLabels.complete).toBe("Complete");
  });

  it("marks every ready lifecycle stage complete", () => {
    expect(lifecyclePresentation({ status: "ready", processing_stage: "complete" }).every((step) => step.state === "complete")).toBe(true);
  });

  it("marks earlier, current, and future processing stages accurately", () => {
    const steps = lifecyclePresentation({ status: "processing", processing_stage: "chunking" });
    expect(steps.find((step) => step.stage === "cleaning")?.state).toBe("complete");
    expect(steps.find((step) => step.stage === "chunking")?.state).toBe("active");
    expect(steps.find((step) => step.stage === "embedding")?.state).toBe("pending");
  });

  it("does not invent failed history without a safe error code", () => {
    expect(lifecyclePresentation({ status: "failed", processing_stage: "failed" }).every((step) => step.state === "pending")).toBe(true);
  });

  it("uses a proven failure operation when a safe code exists", () => {
    const steps = lifecyclePresentation({ status: "failed", processing_stage: "failed", error_code: "indexing_failed" });
    expect(steps.find((step) => step.stage === "embedding")?.state).toBe("complete");
    expect(steps.find((step) => step.stage === "indexing")?.state).toBe("failed");
    expect(steps.find((step) => step.stage === "complete")?.state).toBe("pending");
  });

  it("keeps an unknown processing stage safely pending", () => {
    const steps = lifecyclePresentation({ status: "processing", processing_stage: "unknown" as "received" });
    expect(steps.every((step) => step.state === "pending")).toBe(true);
  });

  it("maps safe failure areas", () => {
    expect(safeErrorCodeLabels.metadata_update_failed).toBe("Metadata persistence");
  });

  it.each([
    [0, "0 B"], [1024, "1.0 KB"], [1_048_576, "1.0 MB"], [-1, "Not available"],
  ])("formats %s bytes as %s", (bytes, expected) => {
    expect(formatDocumentFileSize(bytes)).toBe(expected);
  });

  it("shortens a UUID without losing both ends", () => {
    expect(shortenDocumentId(documentId)).toBe("11111111…1111");
  });

  it("formats valid timestamps and rejects invalid values", () => {
    expect(formatDocumentTimestamp("2026-07-15T18:30:00Z")).not.toBe("Not available");
    expect(formatDocumentTimestamp("invalid")).toBe("Not available");
  });

  it("accepts PDF candidates and rejects obvious non-PDF files", () => {
    expect(isPdfFileCandidate("Policy.PDF", "application/pdf")).toBe(true);
    expect(isPdfFileCandidate("policy.pdf", "")).toBe(true);
    expect(isPdfFileCandidate("policy.txt", "text/plain")).toBe(false);
    expect(isPdfFileCandidate("policy.pdf", "text/plain")).toBe(false);
  });
});

describe("document query state", () => {
  it("trims q and parses valid status and offset", () => {
    expect(parseDocumentQuery(new URLSearchParams("q=%20remote%20&status=ready&offset=20"))).toEqual({ q: "remote", status: "ready", offset: 20 });
  });

  it.each(["unknown", "READY", ""])("falls back from invalid status %s", (status) => {
    expect(parseDocumentQuery(new URLSearchParams({ status })).status).toBeUndefined();
  });

  it.each(["-1", "abc", "1.5", ""])("falls back from invalid offset %s", (offset) => {
    expect(parseDocumentQuery(new URLSearchParams({ offset })).offset).toBe(0);
  });

  it("resets offset when search changes", () => {
    expect(updateDocumentQuery({ q: "", status: "ready", offset: 40 }, { q: "remote" }, true)).toEqual({ q: "remote", status: "ready", offset: 0 });
  });

  it("resets offset when status changes", () => {
    expect(updateDocumentQuery({ q: "remote", offset: 40 }, { status: "failed" }, true).offset).toBe(0);
  });

  it("preserves filters while paging", () => {
    const query = updateDocumentQuery({ q: "remote", status: "ready", offset: 0 }, { offset: 20 });
    expect(documentQueryString(query)).toBe("q=remote&status=ready&offset=20");
  });
});

describe("document pagination", () => {
  it("disables previous at zero and never returns negative offsets", () => {
    expect(previousDocumentOffset(list())).toBeNull();
    expect(previousDocumentOffset(list({ offset: 5 }))).toBe(0);
  });

  it("calculates next offset from the backend limit", () => {
    expect(nextDocumentOffset(list({ items: Array(20).fill({}), total: 37 } as Partial<ParsedDocumentList>))).toBe(20);
  });

  it("disables next on the final result", () => {
    expect(nextDocumentOffset(list({ items: Array(17).fill({}), total: 37, offset: 20 } as Partial<ParsedDocumentList>))).toBeNull();
  });

  it("formats a visible result range", () => {
    expect(documentResultRange(list({ items: Array(17).fill({}), total: 37, offset: 20 } as Partial<ParsedDocumentList>))).toBe("Showing 21–37 of 37");
  });
});

describe("upload error presentation", () => {
  it.each([
    ["DATABASE_UNAVAILABLE", "Document metadata is unavailable"],
    ["extraction_failed", "Text extraction failed"],
    ["indexing_failed", "Evidence indexing failed"],
    ["unknown", "The policy could not be processed"],
  ])("maps %s safely", (code, title) => {
    expect(uploadErrorPresentation(code).title).toBe(title);
  });
});
