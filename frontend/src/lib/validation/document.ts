import { z } from "zod";
import type { components } from "@/lib/api/generated";

export type GeneratedDocumentList = components["schemas"]["DocumentListResponse"];
export type GeneratedDocumentDetail = components["schemas"]["DocumentDetailResponse"];
export type GeneratedDocumentStatus = components["schemas"]["DocumentStatusResponse"];
export type GeneratedDocumentUpload = components["schemas"]["DocumentIngestionResponse"];

export const documentStatuses = ["processing", "ready", "failed"] as const;
export const processingStages = [
  "received",
  "stored",
  "extracting",
  "cleaning",
  "chunking",
  "embedding",
  "indexing",
  "complete",
  "failed",
] as const;

const statusSchema = z.enum(documentStatuses);
const stageSchema = z.enum(processingStages);
const nullableCount = z.number().int().min(0).nullable().optional();
const timestamp = z.string().datetime({ offset: true });
const nullableTimestamp = timestamp.nullable().optional();

const baseDocumentSummarySchema = z.object({
  document_id: z.string().uuid(),
  filename: z.string().min(1).max(512),
  content_type: z.string().min(1).max(255),
  size_bytes: z.number().int().min(0),
  status: statusSchema,
  processing_stage: stageSchema,
  page_count: nullableCount,
  character_count: nullableCount,
  chunk_count: nullableCount,
  created_at: timestamp,
  updated_at: timestamp,
  indexed_at: nullableTimestamp,
});

export const documentSummarySchema: z.ZodType<
  components["schemas"]["DocumentSummaryResponse"]
> = baseDocumentSummarySchema;

export const documentListSchema: z.ZodType<GeneratedDocumentList> = z.object({
  items: z.array(documentSummarySchema),
  total: z.number().int().min(0),
  limit: z.number().int().min(1).max(100),
  offset: z.number().int().min(0),
});

export const documentDetailSchema: z.ZodType<GeneratedDocumentDetail> =
  baseDocumentSummarySchema.extend({
    chroma_collection: z.string().min(1).max(255).nullable().optional(),
    embedding_model: z.string().min(1).max(512).nullable().optional(),
    error_code: z.string().min(1).max(64).nullable().optional(),
    error_message: z.string().min(1).max(500).nullable().optional(),
  });

export const documentStatusSchema: z.ZodType<GeneratedDocumentStatus> = z.object({
  document_id: z.string().uuid(),
  status: statusSchema,
  processing_stage: stageSchema,
  page_count: nullableCount,
  chunk_count: nullableCount,
  error_code: z.string().min(1).max(64).nullable().optional(),
  updated_at: timestamp,
});

export type SafeDocumentUpload = Pick<
  GeneratedDocumentUpload,
  | "success"
  | "document_id"
  | "filename"
  | "content_type"
  | "size_bytes"
  | "page_count"
  | "chunk_count"
  | "status"
  | "processing_stage"
  | "character_count"
  | "duplicate"
  | "created_at"
  | "indexed_at"
  | "message"
>;

export const documentUploadSchema: z.ZodType<SafeDocumentUpload> = z.object({
  success: z.boolean(),
  document_id: z.string().uuid(),
  filename: z.string().min(1).max(512),
  content_type: z.string().min(1).max(255),
  size_bytes: z.number().int().min(0),
  page_count: z.number().int().min(0),
  chunk_count: z.number().int().min(0),
  status: statusSchema,
  processing_stage: stageSchema,
  character_count: nullableCount,
  duplicate: z.boolean(),
  created_at: nullableTimestamp,
  indexed_at: nullableTimestamp,
  message: z.string().min(1).max(1000),
});

export const backendErrorSchema = z.object({
  success: z.boolean().optional(),
  error: z.object({
    code: z.string().min(1).max(80),
    message: z.string().min(1).max(1000),
  }),
});

export type ParsedDocumentList = z.infer<typeof documentListSchema>;
export type ParsedDocumentDetail = z.infer<typeof documentDetailSchema>;
export type ParsedDocumentStatus = z.infer<typeof documentStatusSchema>;
export type ParsedDocumentUpload = z.infer<typeof documentUploadSchema>;
