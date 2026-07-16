"use client";

import Link from "next/link";
import { CircleAlert, Database, FileStack, SearchX, ServerCrash } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import type { DocumentApiErrorCode } from "@/lib/api/documents";
import { cn } from "@/lib/utils";

export function DocumentEmptyState({ filtered, onClear, onUpload }: { filtered: boolean; onClear: () => void; onUpload: () => void }) {
  const Icon = filtered ? SearchX : FileStack;
  return (
    <section className="rounded-xl border border-neutral-200 bg-white px-5 py-10 text-center sm:min-h-[232px] sm:px-8">
      <div className="mx-auto flex size-10 items-center justify-center rounded-lg border border-teal-100 bg-teal-50 text-teal-700"><Icon aria-hidden="true" size={20} /></div>
      <h2 className="mt-4 text-base font-semibold text-neutral-900">{filtered ? "No documents match these filters" : "No policy documents yet"}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-neutral-600">{filtered ? "Change the filename search or status filter." : "Upload a policy PDF to create persistent metadata and searchable evidence."}</p>
      <div className="mt-6"><Button onClick={filtered ? onClear : onUpload}>{filtered ? "Clear filters" : "Upload policy"}</Button></div>
    </section>
  );
}

export function DocumentErrorState({ code, onRetry, detail = false }: { code: DocumentApiErrorCode; onRetry: () => void; detail?: boolean }) {
  const database = code === "DATABASE_UNAVAILABLE";
  const notFound = code === "DOCUMENT_NOT_FOUND";
  const Icon = database ? Database : notFound ? CircleAlert : ServerCrash;
  const title = database ? "Document metadata is unavailable" : notFound ? "Document not found" : "Document service is unavailable";
  const description = database
    ? "PolicyGPT could not reach the document metadata service. Existing indexed Ask capabilities may still remain available."
    : notFound
      ? "The requested document identifier does not match a persistent record."
      : "PolicyGPT could not reach the backend service. Check the local services and try again.";
  return (
    <section className="rounded-xl border border-neutral-200 bg-white px-5 py-10 text-center sm:min-h-[232px] sm:px-8">
      <div className="mx-auto flex size-10 items-center justify-center rounded-lg border border-info-200 bg-info-50 text-info-700"><Icon aria-hidden="true" size={20} /></div>
      <h2 className="mt-4 text-base font-semibold text-neutral-900">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-neutral-600">{description}</p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {!notFound ? <Button onClick={onRetry}>Retry</Button> : null}
        {database && !detail ? <Link href="/ask" className={cn(buttonVariants({ variant: "outline" }))}>Go to Ask PolicyGPT</Link> : null}
        {detail || notFound ? <Link href="/documents" className={cn(buttonVariants({ variant: "outline" }))}>Back to Documents</Link> : null}
      </div>
    </section>
  );
}
