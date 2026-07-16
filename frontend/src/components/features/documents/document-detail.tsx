"use client";

import Link from "next/link";
import { ArrowLeft, FileText, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { DocumentErrorState } from "@/components/features/documents/document-state";
import { DocumentLifecycle } from "@/components/features/documents/document-lifecycle";
import { DocumentStatusBadge } from "@/components/features/documents/document-status-badge";
import { Button, buttonVariants } from "@/components/ui/button";
import type { DocumentApiErrorCode, DocumentDetailPageState } from "@/lib/api/documents";
import { processingStageLabels, safeErrorCodeLabels, type DocumentDetail } from "@/lib/domain/document";
import { formatDocumentCount, formatDocumentFileSize, formatDocumentTimestamp, shortenDocumentId } from "@/lib/formatters/document";
import { backendErrorSchema, documentDetailSchema, documentStatusSchema } from "@/lib/validation/document";
import { cn } from "@/lib/utils";

export function DocumentDetailProduct({ initialState, documentId }: { initialState: DocumentDetailPageState; documentId: string }) {
  const [state, setState] = useState(initialState);
  const [refreshing, startRefresh] = useTransition();
  const inFlight = useRef(false);

  const loadDetail = useCallback(async () => {
    try {
      const response = await fetch(`/api/documents/${encodeURIComponent(documentId)}`, { cache: "no-store", headers: { Accept: "application/json" } });
      const payload: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const parsed = backendErrorSchema.safeParse(payload);
        const raw = parsed.success ? parsed.data.error.code : "BACKEND_UNAVAILABLE";
        const code: DocumentApiErrorCode = raw === "DATABASE_UNAVAILABLE" ? "DATABASE_UNAVAILABLE" : raw === "DOCUMENT_NOT_FOUND" ? "DOCUMENT_NOT_FOUND" : "BACKEND_UNAVAILABLE";
        setState({ state: "error", code });
        return;
      }
      const parsed = documentDetailSchema.safeParse(payload);
      setState(parsed.success ? { state: "ready", data: parsed.data } : { state: "error", code: "INVALID_RESPONSE" });
    } catch {
      setState({ state: "error", code: "BACKEND_UNAVAILABLE" });
    }
  }, [documentId]);

  const processing = state.state === "ready" && state.data.status === "processing";
  useEffect(() => {
    if (!processing) return;
    const timer = window.setInterval(async () => {
      if (document.hidden || inFlight.current) return;
      inFlight.current = true;
      try {
        const response = await fetch(`/api/documents/${encodeURIComponent(documentId)}/status`, { cache: "no-store" });
        const payload: unknown = await response.json().catch(() => null);
        const parsed = documentStatusSchema.safeParse(payload);
        if (response.ok && parsed.success) {
          if (parsed.data.status === "processing") {
            setState((current) => current.state === "ready" ? { state: "ready", data: { ...current.data, status: parsed.data.status, processing_stage: parsed.data.processing_stage, page_count: parsed.data.page_count, chunk_count: parsed.data.chunk_count, updated_at: parsed.data.updated_at } } : current);
          } else {
            await loadDetail();
          }
        }
      } finally {
        inFlight.current = false;
      }
    }, 4500);
    return () => window.clearInterval(timer);
  }, [documentId, loadDetail, processing]);

  if (state.state === "error") return <DocumentErrorState detail code={state.code} onRetry={() => window.location.reload()} />;
  const docData = state.data;
  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <Link href="/documents" className={cn(buttonVariants({ variant: "link" }), "-ml-2 mb-2 px-2")}><ArrowLeft aria-hidden="true" />Back to Documents</Link>
          <div className="flex min-w-0 items-start gap-3">
            <span className="mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-lg border border-neutral-200 bg-white text-teal-700"><FileText aria-hidden="true" size={20} /></span>
            <div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="rounded border border-neutral-200 bg-neutral-50 px-1.5 py-0.5 text-[10px] font-semibold text-neutral-600">PDF</span><DocumentStatusBadge status={docData.status} /></div><h1 className="mt-2 break-words text-2xl font-semibold tracking-[-0.025em] text-neutral-900 sm:text-[28px]">{docData.filename}</h1><p className="font-metric mt-2 break-all text-xs text-neutral-500">{shortenDocumentId(docData.document_id)}</p></div>
          </div>
        </div>
        <Button variant="outline" disabled={refreshing} onClick={() => startRefresh(async () => loadDetail())}><RefreshCw aria-hidden="true" className={refreshing ? "animate-spin" : ""} />{refreshing ? "Refreshing" : "Refresh metadata"}</Button>
      </div>

      <div className="mt-6 grid items-start gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
        <MetadataCard document={docData} />
        <IndexingCard document={docData} />
      </div>
      <div className="mt-5"><DocumentLifecycle document={docData} /></div>
    </>
  );
}

function MetadataCard({ document }: { document: DocumentDetail }) {
  return <section className="rounded-xl border border-neutral-200 bg-white p-5" aria-labelledby="metadata-title"><h2 id="metadata-title" className="text-base font-semibold text-neutral-900">Document metadata</h2><p className="mt-1 text-sm leading-6 text-neutral-600">Persistent source identity and ingestion counts.</p><dl className="mt-4 divide-y divide-neutral-200"><DetailRow label="Document ID" value={document.document_id} mono /><DetailRow label="Content type" value={document.content_type} /><DetailRow label="File size" value={formatDocumentFileSize(document.size_bytes)} mono /><DetailRow label="Page count" value={formatDocumentCount(document.page_count)} mono /><DetailRow label="Character count" value={formatDocumentCount(document.character_count)} mono /><DetailRow label="Chunk count" value={formatDocumentCount(document.chunk_count)} mono /><DetailRow label="Created" value={formatDocumentTimestamp(document.created_at)} mono /><DetailRow label="Updated" value={formatDocumentTimestamp(document.updated_at)} mono /><DetailRow label="Indexed" value={formatDocumentTimestamp(document.indexed_at)} mono /></dl></section>;
}

function IndexingCard({ document }: { document: DocumentDetail }) {
  return <section className="rounded-xl border border-neutral-200 bg-white p-5" aria-labelledby="indexing-title"><h2 id="indexing-title" className="text-base font-semibold text-neutral-900">Evidence indexing</h2><p className="mt-1 text-sm leading-6 text-neutral-600">Safe vector-store and embedding identifiers.</p><dl className="mt-4 divide-y divide-neutral-200"><DetailRow label="Status" value={<DocumentStatusBadge status={document.status} />} /><DetailRow label="Processing stage" value={processingStageLabels[document.processing_stage]} /><DetailRow label="Chroma collection" value={document.chroma_collection ?? "Not available"} mono /><DetailRow label="Embedding model" value={document.embedding_model ?? "Not available"} mono />{document.status === "failed" ? <DetailRow label="Failure area" value={document.error_code ? safeErrorCodeLabels[document.error_code] ?? "Processing failed" : "Processing failed"} /> : null}</dl></section>;
}

function DetailRow({ label, value, mono = false }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return <div className="grid gap-1 py-3 sm:grid-cols-[145px_minmax(0,1fr)] sm:gap-4"><dt className="text-xs font-medium text-neutral-500">{label}</dt><dd className={mono ? "font-metric min-w-0 break-all text-sm text-neutral-800" : "min-w-0 break-words text-sm text-neutral-800"}>{value}</dd></div>;
}
