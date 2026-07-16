import { describe, expect, it } from "vitest";
import {
  backendErrorSchema,
  documentDetailSchema,
  documentListSchema,
  documentStatusSchema,
  documentUploadSchema,
} from "./document";

const summary = {
  document_id: "11111111-1111-4111-8111-111111111111",
  filename: "sample_hr_policy.pdf",
  content_type: "application/pdf",
  size_bytes: 21035,
  status: "ready",
  processing_stage: "complete",
  page_count: 12,
  character_count: 14987,
  chunk_count: 20,
  created_at: "2026-07-15T18:00:00Z",
  updated_at: "2026-07-15T18:01:00Z",
  indexed_at: "2026-07-15T18:01:00Z",
} as const;

describe("document runtime validation", () => {
  it("accepts a valid list", () => {
    expect(documentListSchema.parse({ items: [summary], total: 1, limit: 20, offset: 0 }).items).toHaveLength(1);
  });

  it("accepts valid ready, processing, and failed details", () => {
    expect(documentDetailSchema.safeParse({ ...summary, chroma_collection: "policygpt_documents", embedding_model: "model" }).success).toBe(true);
    expect(documentDetailSchema.safeParse({ ...summary, status: "processing", processing_stage: "extracting", indexed_at: null, page_count: null, chunk_count: null }).success).toBe(true);
    expect(documentDetailSchema.safeParse({ ...summary, status: "failed", processing_stage: "failed", indexed_at: null, error_code: "extraction_failed", error_message: "Text could not be extracted." }).success).toBe(true);
  });

  it("accepts a compact status response", () => {
    expect(documentStatusSchema.safeParse({ document_id: summary.document_id, status: "processing", processing_stage: "indexing", page_count: 12, chunk_count: null, error_code: null, updated_at: summary.updated_at }).success).toBe(true);
  });

  it("accepts new and duplicate upload responses", () => {
    const upload = { success: true, document_id: summary.document_id, filename: summary.filename, content_type: summary.content_type, size_bytes: summary.size_bytes, page_count: 12, chunk_count: 20, status: "ready", processing_stage: "complete", character_count: 14987, duplicate: false, created_at: summary.created_at, indexed_at: summary.indexed_at, message: "Ready" };
    expect(documentUploadSchema.safeParse(upload).success).toBe(true);
    expect(documentUploadSchema.parse({ ...upload, duplicate: true }).duplicate).toBe(true);
  });

  it("accepts a controlled backend error", () => {
    expect(backendErrorSchema.parse({ success: false, error: { code: "DATABASE_UNAVAILABLE", message: "Document metadata is temporarily unavailable." } }).error.code).toBe("DATABASE_UNAVAILABLE");
  });

  it.each([
    { items: "invalid", total: 1, limit: 20, offset: 0 },
    { items: [], total: -1, limit: 20, offset: 0 },
    { items: [], total: 0, limit: 101, offset: 0 },
  ])("rejects malformed lists", (value) => {
    expect(documentListSchema.safeParse(value).success).toBe(false);
  });

  it("rejects malformed detail and upload responses", () => {
    expect(documentDetailSchema.safeParse({ ...summary, document_id: "not-a-uuid" }).success).toBe(false);
    expect(documentUploadSchema.safeParse({ success: true, document_id: summary.document_id }).success).toBe(false);
  });

  it("strips unknown fields from safe detail output", () => {
    const parsed = documentDetailSchema.parse({ ...summary, storage_key: "documents/secret/source.pdf", sha256: "secret" });
    expect(parsed).not.toHaveProperty("storage_key");
    expect(parsed).not.toHaveProperty("sha256");
  });

  it("ignores legacy preview and sample chunk fields in upload output", () => {
    const parsed = documentUploadSchema.parse({ success: true, document_id: summary.document_id, filename: summary.filename, content_type: summary.content_type, size_bytes: summary.size_bytes, page_count: 12, chunk_count: 20, status: "ready", processing_stage: "complete", character_count: 14987, duplicate: false, created_at: summary.created_at, indexed_at: summary.indexed_at, message: "Ready", preview_text: "sensitive source", sample_chunks: [{ text: "sensitive chunk" }] });
    expect(parsed).not.toHaveProperty("preview_text");
    expect(parsed).not.toHaveProperty("sample_chunks");
  });
});
