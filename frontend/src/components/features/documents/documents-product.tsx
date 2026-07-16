"use client";

import Link from "next/link";
import { Database, FileArchive, FileText, RefreshCw, Search, Server, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { DocumentEmptyState, DocumentErrorState } from "@/components/features/documents/document-state";
import { DocumentPagination } from "@/components/features/documents/document-pagination";
import { DocumentStatusBadge } from "@/components/features/documents/document-status-badge";
import { DocumentUploadDialog } from "@/components/features/documents/document-upload-dialog";
import { PageHeader } from "@/components/system/page-header";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { DocumentApiErrorCode, DocumentListPageState } from "@/lib/api/documents";
import {
  documentQueryString,
  processingStageLabels,
  updateDocumentQuery,
  type DocumentQuery,
  type DocumentSummary,
} from "@/lib/domain/document";
import { formatDocumentCount, formatDocumentFileSize, formatDocumentTimestamp, shortenDocumentId } from "@/lib/formatters/document";
import { backendErrorSchema, documentListSchema } from "@/lib/validation/document";
import { cn } from "@/lib/utils";

function registryUrl(query: DocumentQuery): string {
  const params = documentQueryString(query);
  return params ? `/documents?${params}` : "/documents";
}

function bffUrl(query: DocumentQuery): string {
  const params = new URLSearchParams({ limit: "20", offset: String(query.offset) });
  if (query.q) params.set("q", query.q);
  if (query.status) params.set("status", query.status);
  return `/api/documents?${params.toString()}`;
}

export function DocumentsProduct({
  initialState,
  query,
}: {
  initialState: DocumentListPageState;
  query: DocumentQuery;
}) {
  const router = useRouter();
  const [state, setState] = useState(initialState);
  const [search, setSearch] = useState(query.q);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [refreshing, startRefresh] = useTransition();
  const firstSearch = useRef(true);
  const pollInFlight = useRef(false);

  const navigate = useCallback((next: DocumentQuery) => {
    router.replace(registryUrl(next), { scroll: false });
  }, [router]);

  const refreshRegistry = useCallback(async () => {
    try {
      const response = await fetch(bffUrl(query), { headers: { Accept: "application/json" }, cache: "no-store" });
      const payload: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const parsed = backendErrorSchema.safeParse(payload);
        const rawCode = parsed.success ? parsed.data.error.code : "BACKEND_UNAVAILABLE";
        const code: DocumentApiErrorCode = rawCode === "DATABASE_UNAVAILABLE" ? "DATABASE_UNAVAILABLE" : "BACKEND_UNAVAILABLE";
        setState({ state: "error", code });
        return;
      }
      const parsed = documentListSchema.safeParse(payload);
      setState(parsed.success ? { state: "ready", data: parsed.data } : { state: "error", code: "INVALID_RESPONSE" });
    } catch {
      setState({ state: "error", code: "BACKEND_UNAVAILABLE" });
    }
  }, [query]);

  useEffect(() => {
    if (firstSearch.current) {
      firstSearch.current = false;
      return;
    }
    const timer = window.setTimeout(() => {
      navigate(updateDocumentQuery(query, { q: search }, true));
    }, 350);
    return () => window.clearTimeout(timer);
  }, [navigate, query, search]);

  const hasProcessing = state.state === "ready" && state.data.items.some((item) => item.status === "processing");
  useEffect(() => {
    if (!hasProcessing) return;
    const timer = window.setInterval(async () => {
      if (document.hidden || pollInFlight.current) return;
      pollInFlight.current = true;
      await refreshRegistry();
      pollInFlight.current = false;
    }, 4500);
    return () => window.clearInterval(timer);
  }, [hasProcessing, refreshRegistry]);

  function refresh() {
    startRefresh(async () => refreshRegistry());
  }

  function clearFilters() {
    setSearch("");
    navigate({ q: "", offset: 0 });
  }

  const filtered = Boolean(query.q || query.status || query.offset);
  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <PageHeader title="Documents" description="Manage policy sources, ingestion status, and indexed evidence." className="mb-0" />
        <DocumentUploadDialog open={uploadOpen} onOpenChange={setUploadOpen} onUploaded={refreshRegistry} />
      </div>

      <SourceTruthStrip />

      <section className="mt-5 rounded-xl border border-neutral-200 bg-white p-4" aria-label="Document registry controls">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <label className="relative min-w-0 flex-1 lg:max-w-md">
            <span className="sr-only">Search documents by filename</span>
            <Search aria-hidden="true" className="absolute top-2 left-2.5 text-neutral-400" size={16} />
            <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search filenames" className="pl-8" />
          </label>
          <label>
            <span className="sr-only">Filter documents by status</span>
            <select aria-label="Filter documents by status" value={query.status ?? "all"} onChange={(event) => navigate(updateDocumentQuery(query, { q: search, status: event.target.value === "all" ? undefined : event.target.value as DocumentQuery["status"] }, true))} className="h-8 w-full rounded-lg border border-neutral-300 bg-white px-2.5 text-sm text-neutral-700 outline-none focus-visible:border-teal-700 focus-visible:ring-2 focus-visible:ring-teal-700/20 lg:w-44">
              <option value="all">All documents</option><option value="ready">Ready</option><option value="processing">Processing</option><option value="failed">Failed</option>
            </select>
          </label>
          <Button variant="outline" onClick={refresh} disabled={refreshing} aria-label="Refresh document registry">
            <RefreshCw aria-hidden="true" className={refreshing ? "animate-spin" : ""} />{refreshing ? "Refreshing" : "Refresh"}
          </Button>
          {filtered ? <Button variant="ghost" onClick={clearFilters}><X aria-hidden="true" />Clear filters</Button> : null}
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-sm text-neutral-600">
          <span aria-live="polite">{state.state === "ready" ? <><span className="font-metric font-semibold text-neutral-900">{state.data.total}</span> persistent document{state.data.total === 1 ? "" : "s"}</> : "Registry unavailable"}</span>
          {query.q || query.status ? <span>Filters: {query.q ? `filename “${query.q}”` : ""}{query.q && query.status ? " · " : ""}{query.status ? query.status : ""}</span> : null}
        </div>
      </section>

      <div className="mt-4" aria-busy={refreshing}>
        {state.state === "error" ? <DocumentErrorState code={state.code} onRetry={refresh} /> : state.data.items.length === 0 ? <DocumentEmptyState filtered={filtered} onClear={clearFilters} onUpload={() => setUploadOpen(true)} /> : <DocumentRegistry data={state.data.items} />}
        {state.state === "ready" && (state.data.items.length > 0 || state.data.offset > 0) ? <div className="rounded-b-xl border border-t-0 border-neutral-200 bg-white"><DocumentPagination data={state.data} onOffset={(offset) => navigate(updateDocumentQuery(query, { offset }))} /></div> : null}
      </div>
    </>
  );
}

function SourceTruthStrip() {
  const items = [
    { label: "PostgreSQL", detail: "Metadata source of truth", icon: Database },
    { label: "Local source storage", detail: "Original PDF source", icon: FileArchive },
    { label: "ChromaDB", detail: "Indexed retrieval evidence", icon: Server },
  ];
  return <section className="mt-6 grid gap-3 sm:grid-cols-3" aria-label="Document architecture responsibilities">{items.map(({ label, detail, icon: Icon }) => <div key={label} className="flex items-center gap-3 rounded-xl border border-neutral-200 bg-white px-4 py-3"><span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-navy-50 text-navy-800"><Icon aria-hidden="true" size={18} /></span><div className="min-w-0"><div className="text-sm font-semibold text-neutral-900">{label}</div><div className="text-xs leading-5 text-neutral-600">{detail}</div></div></div>)}</section>;
}

function DocumentRegistry({ data }: { data: DocumentSummary[] }) {
  return <>
    <div className="hidden overflow-hidden rounded-t-xl border border-neutral-200 bg-white lg:block">
      <Table><TableHeader><TableRow><TableHead className="pl-4">Document</TableHead><TableHead>Status</TableHead><TableHead>Pages</TableHead><TableHead>Chunks</TableHead><TableHead className="hidden xl:table-cell">File size</TableHead><TableHead className="hidden xl:table-cell">Added</TableHead><TableHead className="hidden 2xl:table-cell">Updated</TableHead><TableHead className="pr-4 text-right">Action</TableHead></TableRow></TableHeader><TableBody>
        {data.map((document) => <TableRow key={document.document_id}>
          <TableCell className="max-w-[360px] py-3 pl-4 whitespace-normal"><div className="flex min-w-0 items-start gap-3"><span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-neutral-100 text-neutral-600"><FileText aria-hidden="true" size={16} /></span><div className="min-w-0"><div className="break-words font-medium text-neutral-900">{document.filename}</div><div className="mt-1 flex flex-wrap items-center gap-2"><span className="rounded border border-neutral-200 bg-neutral-50 px-1.5 py-0.5 text-[10px] font-semibold text-neutral-600">PDF</span><span className="font-metric text-xs text-neutral-500">{shortenDocumentId(document.document_id)}</span></div></div></div></TableCell>
          <TableCell className="whitespace-normal"><DocumentStatusBadge status={document.status} /><div className="mt-1.5 text-xs text-neutral-600">{processingStageLabels[document.processing_stage]}</div></TableCell>
          <TableCell className="font-metric">{formatDocumentCount(document.page_count)}</TableCell><TableCell className="font-metric">{formatDocumentCount(document.chunk_count)}</TableCell>
          <TableCell className="font-metric hidden xl:table-cell">{formatDocumentFileSize(document.size_bytes)}</TableCell><TableCell className="font-metric hidden text-xs xl:table-cell">{formatDocumentTimestamp(document.created_at, "short")}</TableCell><TableCell className="font-metric hidden text-xs 2xl:table-cell">{formatDocumentTimestamp(document.updated_at, "short")}</TableCell>
          <TableCell className="pr-4 text-right"><Link href={`/documents/${document.document_id}`} className={cn(buttonVariants({ variant: "outline" }))} aria-label={`Open details for ${document.filename}`}>Open details</Link></TableCell>
        </TableRow>)}
      </TableBody></Table>
    </div>
    <div className="space-y-3 lg:hidden">{data.map((document) => <article key={document.document_id} className="rounded-xl border border-neutral-200 bg-white p-4"><div className="flex min-w-0 items-start justify-between gap-3"><div className="min-w-0"><div className="break-words text-sm font-semibold text-neutral-900">{document.filename}</div><div className="font-metric mt-1 break-all text-xs text-neutral-500">{shortenDocumentId(document.document_id)}</div></div><DocumentStatusBadge status={document.status} /></div><div className="mt-3 text-xs text-neutral-600">{processingStageLabels[document.processing_stage]}</div><dl className="mt-4 grid grid-cols-2 gap-3 text-sm"><MobileMetric label="Pages" value={formatDocumentCount(document.page_count)} /><MobileMetric label="Chunks" value={formatDocumentCount(document.chunk_count)} /><MobileMetric label="File size" value={formatDocumentFileSize(document.size_bytes)} /><MobileMetric label="Added" value={formatDocumentTimestamp(document.created_at, "short")} /></dl><Link href={`/documents/${document.document_id}`} className={cn(buttonVariants({ variant: "outline" }), "mt-4 w-full")} aria-label={`Open details for ${document.filename}`}>Open details</Link></article>)}</div>
  </>;
}

function MobileMetric({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-xs text-neutral-500">{label}</dt><dd className="font-metric mt-1 break-words text-xs font-medium text-neutral-800">{value}</dd></div>;
}
