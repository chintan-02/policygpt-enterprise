"use client";

import Link from "next/link";
import { CheckCircle2, FileText, LoaderCircle, Plus, RefreshCw, Trash2, TriangleAlert } from "lucide-react";
import { useRef, useState } from "react";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { DocumentStatusBadge } from "@/components/features/documents/document-status-badge";
import { isPdfFileCandidate, uploadErrorPresentation, type DocumentUploadResult } from "@/lib/domain/document";
import { formatDocumentCount, formatDocumentFileSize, formatDocumentTimestamp, shortenDocumentId } from "@/lib/formatters/document";
import { backendErrorSchema, documentUploadSchema } from "@/lib/validation/document";
import { cn } from "@/lib/utils";

type UploadState =
  | { state: "idle" }
  | { state: "selected"; file: File }
  | { state: "uploading"; file: File }
  | { state: "success"; result: DocumentUploadResult }
  | { state: "error"; file: File | null; code: string };

export function DocumentUploadDialog({
  open,
  onOpenChange,
  onUploaded,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploaded: () => Promise<void>;
}) {
  const [upload, setUpload] = useState<UploadState>({ state: "idle" });
  const inputRef = useRef<HTMLInputElement>(null);
  const active = upload.state === "uploading";

  function reset() {
    setUpload({ state: "idle" });
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleOpenChange(next: boolean) {
    if (active) return;
    onOpenChange(next);
    if (!next) reset();
  }

  function selectFile(file: File | undefined) {
    if (!file) return;
    if (!isPdfFileCandidate(file.name, file.type)) {
      setUpload({ state: "error", file: null, code: "UNSUPPORTED_FILE_TYPE" });
      return;
    }
    setUpload({ state: "selected", file });
  }

  async function submit(file: File) {
    if (active) return;
    setUpload({ state: "uploading", file });
    const body = new FormData();
    body.set("file", file, file.name);
    try {
      const response = await fetch("/api/documents/upload", {
        method: "POST",
        body,
        headers: { Accept: "application/json" },
      });
      const payload: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const parsedError = backendErrorSchema.safeParse(payload);
        setUpload({
          state: "error",
          file,
          code: parsedError.success ? parsedError.data.error.code : "REQUEST_FAILED",
        });
        return;
      }
      const parsed = documentUploadSchema.safeParse(payload);
      if (!parsed.success) {
        setUpload({ state: "error", file, code: "INVALID_RESPONSE" });
        return;
      }
      setUpload({ state: "success", result: parsed.data });
      await onUploaded();
    } catch {
      setUpload({ state: "error", file, code: "BACKEND_UNAVAILABLE" });
    }
  }

  const error = upload.state === "error" ? uploadErrorPresentation(upload.code) : null;
  const result = upload.state === "success" ? upload.result : null;
  const errorClasses = error?.tone === "info"
    ? "border-info-200 bg-info-50 text-info-700"
    : error?.tone === "warning"
      ? "border-warning-200 bg-warning-50 text-warning-700"
      : "border-error-200 bg-error-50 text-error-700";

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetTrigger render={<Button size="lg" aria-label="Upload one policy PDF" />}>
        <Plus aria-hidden="true" /> Upload policy
      </SheetTrigger>
      <SheetContent className="w-[min(100vw,460px)] sm:max-w-[460px]" showCloseButton={!active}>
        <SheetHeader className="border-b border-neutral-200 px-5 py-5 pr-12">
          <SheetTitle className="text-lg">Upload policy</SheetTitle>
          <SheetDescription className="mt-1 leading-6">Add one PDF to persistent metadata, source storage, and indexed evidence.</SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-5 py-2">
          {upload.state === "idle" ? (
            <div className="py-5">
              <label htmlFor="policy-pdf" className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-neutral-300 bg-neutral-50 px-5 text-center hover:border-teal-700 hover:bg-teal-50/40 focus-within:ring-2 focus-within:ring-teal-700/20">
                <span className="flex size-10 items-center justify-center rounded-lg border border-teal-100 bg-white text-teal-700"><FileText aria-hidden="true" size={20} /></span>
                <span className="mt-3 text-sm font-semibold text-neutral-900">Select a policy PDF</span>
                <span className="mt-1 text-xs leading-5 text-neutral-600">One document per upload. Server-side upload limits apply.</span>
                <input ref={inputRef} id="policy-pdf" type="file" accept="application/pdf,.pdf" className="sr-only" onChange={(event) => selectFile(event.target.files?.[0])} />
              </label>
              <p className="mt-4 text-sm leading-6 text-neutral-600">Extraction and synchronous evidence indexing may take a moment. Progress remains indeterminate until the backend confirms completion.</p>
            </div>
          ) : null}

          {upload.state === "selected" || upload.state === "uploading" ? (
            <div className="py-5" aria-live="polite">
              <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
                <div className="flex min-w-0 items-start gap-3">
                  <FileText aria-hidden="true" className="mt-0.5 shrink-0 text-teal-700" size={20} />
                  <div className="min-w-0 flex-1"><div className="break-words text-sm font-semibold text-neutral-900">{upload.file.name}</div><div className="font-metric mt-1 text-xs text-neutral-600">{formatDocumentFileSize(upload.file.size)}</div></div>
                  {upload.state === "selected" ? <Button variant="ghost" size="icon-sm" onClick={reset} aria-label={`Remove ${upload.file.name}`}><Trash2 aria-hidden="true" /></Button> : null}
                </div>
              </div>
              {upload.state === "uploading" ? (
                <div className="mt-5 rounded-xl border border-info-200 bg-info-50 p-4 text-info-700" role="status" aria-busy="true">
                  <div className="flex items-center gap-2 text-sm font-semibold"><LoaderCircle aria-hidden="true" className="animate-spin" size={18} />Uploading and indexing policy evidence…</div>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-info-100"><div className="h-full w-full animate-pulse rounded-full bg-info-600/70" /></div>
                  <p className="mt-3 text-xs leading-5">Waiting for extraction, chunking, embedding, and indexing confirmation.</p>
                </div>
              ) : null}
            </div>
          ) : null}

          {result ? (
            <div className="py-5" aria-live="polite">
              <div className={result.duplicate ? "rounded-xl border border-warning-200 bg-warning-50 p-4 text-warning-700" : "rounded-xl border border-success-200 bg-success-50 p-4 text-success-700"}>
                {result.duplicate ? <TriangleAlert aria-hidden="true" size={22} /> : <CheckCircle2 aria-hidden="true" size={22} />}
                <h3 className="mt-3 text-base font-semibold">{result.duplicate ? "Document already indexed" : "Policy indexed successfully"}</h3>
                <p className="mt-1 text-sm leading-6">{result.duplicate ? "PolicyGPT found identical file content and returned the existing record without creating duplicate metadata or vectors." : "The source, persistent metadata, and searchable evidence are ready."}</p>
              </div>
              <dl className="mt-4 divide-y divide-neutral-200 rounded-xl border border-neutral-200 bg-white px-4">
                <ResultRow label="Document" value={result.filename} />
                <ResultRow label="Status" value={<DocumentStatusBadge status={result.status} />} />
                <ResultRow label="Pages" value={formatDocumentCount(result.page_count)} mono />
                <ResultRow label="Chunks" value={formatDocumentCount(result.chunk_count)} mono />
                <ResultRow label="Document ID" value={shortenDocumentId(result.document_id)} mono />
                <ResultRow label="Indexed" value={formatDocumentTimestamp(result.indexed_at)} mono />
              </dl>
            </div>
          ) : null}

          {error ? (
            <div className="py-5" aria-live="assertive">
              <div className={`rounded-xl border p-4 ${errorClasses}`}>
                <TriangleAlert aria-hidden="true" size={22} />
                <h3 className="mt-3 text-base font-semibold">{error.title}</h3>
                <p className="mt-1 text-sm leading-6">{error.message}</p>
              </div>
            </div>
          ) : null}
        </div>

        <SheetFooter className="border-t border-neutral-200 px-5 py-4">
          {upload.state === "selected" ? <Button onClick={() => submit(upload.file)}>Upload and index</Button> : null}
          {upload.state === "selected" ? <label htmlFor="policy-pdf-replace" className="inline-flex h-8 cursor-pointer items-center justify-center rounded-lg border border-neutral-200 px-2.5 text-sm font-medium hover:bg-neutral-100">Replace file<input id="policy-pdf-replace" type="file" accept="application/pdf,.pdf" className="sr-only" onChange={(event) => selectFile(event.target.files?.[0])} /></label> : null}
          {upload.state === "uploading" ? <Button disabled><LoaderCircle aria-hidden="true" className="animate-spin" />Processing</Button> : null}
          {result ? <Link href={`/documents/${result.document_id}`} className={cn(buttonVariants())}>{result.duplicate ? "View existing document" : "View document"}</Link> : null}
          {result ? <Button variant="outline" onClick={() => handleOpenChange(false)}>Done</Button> : null}
          {upload.state === "error" && upload.file ? <Button onClick={() => submit(upload.file!)}><RefreshCw aria-hidden="true" />Try upload again</Button> : null}
          {upload.state === "error" ? <Button variant="outline" onClick={reset}>Choose another file</Button> : null}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

function ResultRow({ label, value, mono = false }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return <div className="grid grid-cols-[100px_minmax(0,1fr)] gap-3 py-3"><dt className="text-xs font-medium text-neutral-500">{label}</dt><dd className={mono ? "font-metric min-w-0 break-words text-sm text-neutral-800" : "min-w-0 break-words text-sm text-neutral-800"}>{value}</dd></div>;
}
