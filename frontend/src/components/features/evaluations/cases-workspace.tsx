"use client";

import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { Filter, Search } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { DiagnosticPill } from "@/components/features/evaluations/evaluation-shared";
import { EngineeringPanel } from "@/components/policygpt/engineering-panel";
import { StatusPill } from "@/components/policygpt/status-pill";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverHeader,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  evaluationCasePresentation,
  filterEvaluationCases,
  selectCaseFromSearch,
  type EvaluationCaseView,
  type EvaluationFilters,
  type EvaluationViewModel,
} from "@/lib/domain/evaluation";
import {
  businessLabel,
  evaluationLabel,
  formatEvaluationLatency,
  formatEvaluationPercent,
  formatEvaluationScore,
  formatPages,
} from "@/lib/formatters/evaluation";

const selectClass = "h-8 min-w-0 rounded-lg border border-neutral-300 bg-white px-2.5 text-sm text-neutral-700 outline-none focus-visible:border-teal-700 focus-visible:ring-2 focus-visible:ring-teal-700/20";

function unique(cases: EvaluationCaseView[], key: "category" | "difficulty" | "evidence_status" | "llm_provider") {
  return [...new Set(cases.map((item) => item[key]))].sort();
}

function FilterSelect({ label, value, options, onChange }: { label: string; value: string; options: Array<{ value: string; label: string }>; onChange: (value: string) => void }) {
  return (
    <label className="min-w-0">
      <span className="sr-only">{label}</span>
      <select aria-label={label} className={selectClass} value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </label>
  );
}

function DetailRow({ label, children, mono = false }: { label: string; children: React.ReactNode; mono?: boolean }) {
  return (
    <div className="grid gap-1 border-t border-neutral-200 py-2.5 first:border-0 sm:grid-cols-[150px_minmax(0,1fr)]">
      <dt className="text-xs font-medium tracking-wide text-neutral-500 uppercase">{label}</dt>
      <dd className={mono ? "font-metric min-w-0 break-words text-sm text-neutral-800" : "min-w-0 break-words text-sm text-neutral-800"}>{children}</dd>
    </div>
  );
}

function CaseSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-neutral-200 pt-4 first:border-0 first:pt-0">
      <h3 className="text-sm font-semibold text-neutral-900">{title}</h3>
      <div className="mt-2">{children}</div>
    </section>
  );
}

function CaseDrawer({ evaluationCase, onOpenChange }: { evaluationCase: EvaluationCaseView | null; onOpenChange: (open: boolean) => void }) {
  const breakdown = evaluationCase?.confidence_breakdown;
  const directSupport = evaluationCase?.direct_support ?? breakdown?.direct_support;
  const presentation = evaluationCase
    ? evaluationCasePresentation(evaluationCase)
    : null;
  return (
    <Sheet open={Boolean(evaluationCase)} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full max-w-none gap-0 overflow-y-auto sm:max-w-[620px]">
        {evaluationCase ? (
          <>
            <SheetHeader className="border-b border-neutral-200 px-5 py-4 pr-14">
              <SheetTitle>Evaluation case {evaluationCase.id}</SheetTitle>
              <SheetDescription>Benchmark decision, evidence validation, answer completeness, confidence, and provider outcome.</SheetDescription>
            </SheetHeader>
            <div className="space-y-5 p-5">
              <CaseSection title="Case summary">
                <div className="flex flex-wrap gap-2">
                  {presentation ? <StatusPill status={presentation.overall.status} label={presentation.overall.label} /> : null}
                  <DiagnosticPill diagnostic={evaluationCase.diagnostic} />
                </div>
              </CaseSection>
              <CaseSection title="Question">
                <p className="text-sm leading-6 text-neutral-700">{evaluationCase.question}</p>
              </CaseSection>
              <CaseSection title="Decision">
                <dl>
                  <DetailRow label="Should answer">{evaluationCase.should_answer ? "Yes" : "No"}</DetailRow>
                  <DetailRow label="Answer ready">{evaluationCase.answer_ready ? "Yes" : "No"}</DetailRow>
                  <DetailRow label="Evidence status">{businessLabel(evaluationCase.evidence_status)}</DetailRow>
                  <DetailRow label="Decision correct">{evaluationCase.readiness_correct ? "Yes" : "No"}</DetailRow>
                  <DetailRow label="Evidence result">{presentation?.evidence.label}</DetailRow>
                  <DetailRow label="Safety result">{presentation?.safety.label}</DetailRow>
                  <DetailRow label="Provider result">{presentation?.provider.label}</DetailRow>
                </dl>
              </CaseSection>
              <CaseSection title="Answer">
                <p className="whitespace-pre-wrap text-sm leading-6 text-neutral-700">{evaluationCase.answer || "No answer was returned."}</p>
              </CaseSection>
              <CaseSection title="Evidence validation">
                <dl>
                  <DetailRow label="Expected pages" mono>{formatPages(evaluationCase.expected_pages)}</DetailRow>
                  <DetailRow label="Retrieved pages" mono>{formatPages(evaluationCase.retrieved_pages)}</DetailRow>
                  <DetailRow label="Expected page found">{evaluationCase.page_hit === null || evaluationCase.page_hit === undefined ? "Not applicable" : evaluationCase.page_hit ? "Yes" : "No"}</DetailRow>
                  <DetailRow label="Citations" mono>{evaluationCase.citation_count}</DetailRow>
                </dl>
              </CaseSection>
              <CaseSection title="Answer completeness">
                <dl>
                  <DetailRow label="Keyword coverage">{formatEvaluationPercent(evaluationCase.keyword_match_score, evaluationCase.expected_answer_keywords.length)}</DetailRow>
                  <DetailRow label="Matched">{evaluationCase.matched_keywords.join(", ") || "None"}</DetailRow>
                  <DetailRow label="Missing">{evaluationCase.missing_keywords.join(", ") || "None"}</DetailRow>
                </dl>
              </CaseSection>
              <CaseSection title="Confidence">
                <dl>
                  <DetailRow label="Evidence confidence">{businessLabel(evaluationCase.evidence_status)}</DetailRow>
                  <DetailRow label="Calibrated score" mono>{formatEvaluationPercent(evaluationCase.confidence_score)}</DetailRow>
                  <DetailRow label="Direct support">{directSupport === true ? "Yes" : directSupport === false ? "No" : "Not measured"}</DetailRow>
                </dl>
              </CaseSection>
              <CaseSection title="Provider diagnostics">
                <dl>
                  <DetailRow label="Generation mode">{presentation?.provider.label}</DetailRow>
                  <DetailRow label="Model" mono>{evaluationCase.model_name ?? "N/A"}</DetailRow>
                  <DetailRow label="Citation fallback">{evaluationCase.providerFallbackDetected ? "Used" : "Not used"}</DetailRow>
                  <DetailRow label="Generation status">{evaluationCase.generation_error_type ? evaluationLabel(evaluationCase.generation_error_type) : evaluationCase.providerFallbackDetected ? "Provider unavailable — citation-only fallback" : "Completed"}</DetailRow>
                </dl>
              </CaseSection>
              <EngineeringPanel title="Engineering details">
                <dl>
                  <DetailRow label="Top retrieval" mono>{formatEvaluationScore(evaluationCase.top_retrieval_score ?? breakdown?.top_retrieval_score, 4)}</DetailRow>
                  <DetailRow label="Average retrieval" mono>{formatEvaluationScore(evaluationCase.average_retrieval_score ?? breakdown?.average_retrieval_score, 4)}</DetailRow>
                  <DetailRow label="Retrieval margin" mono>{formatEvaluationScore(evaluationCase.retrieval_margin ?? breakdown?.retrieval_margin, 4)}</DetailRow>
                  <DetailRow label="Lexical coverage" mono>{formatEvaluationScore(evaluationCase.lexical_coverage ?? breakdown?.lexical_coverage, 4)}</DetailRow>
                  <DetailRow label="Numeric mismatch">{evaluationCase.numeric_mismatch || breakdown?.numeric_mismatch ? "true" : "false"}</DetailRow>
                  <DetailRow label="Numeric claims">{breakdown?.evidence_numeric_claims.join(", ") || "None"}</DetailRow>
                  <DetailRow label="Scope risk">{evaluationCase.scope_risk || breakdown?.scope_risk ? "true" : "false"}</DetailRow>
                  <DetailRow label="Scope reason">{breakdown?.scope_risk_reason ?? "None"}</DetailRow>
                  <DetailRow label="Decision reasons">{evaluationCase.decision_reasons.join(" ") || breakdown?.decision_reasons.join(" ") || "None"}</DetailRow>
                  <DetailRow label="Evaluation focus">{evaluationCase.evaluation_focus.join(", ") || "None"}</DetailRow>
                </dl>
              </EngineeringPanel>
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

export function CasesWorkspace({ data }: { data: EvaluationViewModel }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [sorting, setSorting] = useState<SortingState>([
    { id: "result", desc: false },
    { id: "case", desc: false },
  ]);

  const filters: EvaluationFilters = {
    status: searchParams.get("status") ?? "all",
    support: searchParams.get("support") ?? "all",
    diagnostic: searchParams.get("diagnostic") ?? "all",
    category: searchParams.get("category") ?? "all",
    search: searchParams.get("search") ?? "",
    difficulty: searchParams.get("difficulty") ?? "all",
    evidence: searchParams.get("evidence") ?? "all",
    provider: searchParams.get("provider") ?? "all",
    fallback: searchParams.get("fallback") ?? "all",
    numericMismatch: searchParams.get("numericMismatch") ?? "all",
    scopeRisk: searchParams.get("scopeRisk") ?? "all",
    directSupport: searchParams.get("directSupport") ?? "all",
  };

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams.toString());
    if (!value || value === "all") next.delete(key);
    else next.set(key, value);
    const query = next.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  function openCase(id: string) {
    updateParam("case", id);
  }

  const filtered = filterEvaluationCases(data.results, filters);
  const selected = selectCaseFromSearch(data.results, searchParams.get("case"));
  const columns: ColumnDef<EvaluationCaseView>[] = [
    { id: "case", accessorKey: "id", header: "Case", cell: ({ row }) => <span className="font-metric text-xs text-neutral-700">{row.original.id}</span> },
    { id: "question", accessorKey: "question", header: "Question", cell: ({ row }) => <button type="button" className="max-w-[320px] text-left text-sm leading-5 font-medium whitespace-normal text-neutral-800 hover:text-teal-800 hover:underline" onClick={() => openCase(row.original.id)} aria-label={`Open evaluation case ${row.original.id}`}>{row.original.question}</button> },
    { id: "category", accessorKey: "category", header: "Category", cell: ({ row }) => businessLabel(row.original.category) },
    { id: "difficulty", accessorKey: "difficulty", header: "Difficulty", cell: ({ row }) => businessLabel(row.original.difficulty) },
    { id: "expected", accessorFn: (row) => row.should_answer, header: "Expected behavior", cell: ({ row }) => row.original.should_answer ? "Answer" : "Safe fallback" },
    { id: "diagnostic", accessorKey: "diagnostic", header: "Diagnostic", cell: ({ row }) => <DiagnosticPill diagnostic={row.original.diagnostic} /> },
    { id: "evidence", accessorKey: "evidence_status", header: "Evidence", cell: ({ row }) => evaluationCasePresentation(row.original).evidence.label },
    { id: "safety", header: "Safety", cell: ({ row }) => evaluationCasePresentation(row.original).safety.label },
    { id: "confidence", accessorKey: "confidence_score", header: "Confidence", cell: ({ row }) => <span className="font-metric">{formatEvaluationPercent(row.original.confidence_score)}</span> },
    { id: "provider", accessorKey: "llm_provider", header: "Generation mode", cell: ({ row }) => <span title={row.original.providerFallbackDetected ? "Evidence passed, but a generated answer was unavailable." : undefined}>{row.original.providerFallbackDetected ? "Citation-only" : evaluationCasePresentation(row.original).provider.label}</span> },
    { id: "latency", accessorKey: "latency_ms", header: "Latency", cell: ({ row }) => <span className="font-metric">{formatEvaluationLatency(row.original.latency_ms)}</span> },
    { id: "result", accessorFn: (row) => row.case_passed, header: "Result", cell: ({ row }) => { const result = evaluationCasePresentation(row.original).overall; return <StatusPill compact status={result.status} label={result.label} />; } },
  ];

  // TanStack Table intentionally returns stateful functions that the React Compiler does not memoize.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({ data: filtered, columns, state: { sorting }, onSortingChange: setSorting, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel() });
  const primaryOptions = {
    status: [{ value: "all", label: "All statuses" }, { value: "review", label: "Needs review" }, { value: "passed", label: "Passed" }],
    support: [{ value: "all", label: "All support types" }, { value: "supported", label: "Supported" }, { value: "unsupported", label: "Unsupported" }],
    diagnostic: [{ value: "all", label: "All diagnostics" }, ...[...new Set(data.results.map((item) => item.diagnostic))].sort().map((value) => ({ value, label: evaluationLabel(value) }))],
    category: [{ value: "all", label: "All categories" }, ...unique(data.results, "category").map((value) => ({ value, label: businessLabel(value) }))],
  };
  const booleanOptions = [{ value: "all", label: "All" }, { value: "true", label: "Yes" }, { value: "false", label: "No" }];

  return (
    <>
      <div className="rounded-xl border border-neutral-200 bg-white p-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
          <div className="relative min-w-0 flex-1 xl:max-w-sm">
            <Search aria-hidden="true" className="absolute top-2 left-2.5 text-neutral-400" size={16} />
            <Input aria-label="Search evaluation cases" value={filters.search} onChange={(event) => updateParam("search", event.target.value)} placeholder="Search case, question, or category" className="pl-8" />
          </div>
          <div className="hidden flex-wrap gap-2 md:flex">
            <FilterSelect label="Status" value={filters.status ?? "all"} options={primaryOptions.status} onChange={(value) => updateParam("status", value)} />
            <FilterSelect label="Support type" value={filters.support ?? "all"} options={primaryOptions.support} onChange={(value) => updateParam("support", value)} />
            <FilterSelect label="Diagnostic reason" value={filters.diagnostic ?? "all"} options={primaryOptions.diagnostic} onChange={(value) => updateParam("diagnostic", value)} />
            <FilterSelect label="Category" value={filters.category ?? "all"} options={primaryOptions.category} onChange={(value) => updateParam("category", value)} />
          </div>
          <Popover>
            <PopoverTrigger render={<Button variant="outline" aria-label="Open advanced case filters" />}>
              <Filter aria-hidden="true" />
              Filters
            </PopoverTrigger>
            <PopoverContent align="end" className="w-[min(92vw,360px)] p-4">
              <PopoverHeader><PopoverTitle>Case filters</PopoverTitle><PopoverDescription>Primary and engineering-aware filters update the URL.</PopoverDescription></PopoverHeader>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="md:hidden"><FilterSelect label="Status" value={filters.status ?? "all"} options={primaryOptions.status} onChange={(value) => updateParam("status", value)} /></div>
                <div className="md:hidden"><FilterSelect label="Support type" value={filters.support ?? "all"} options={primaryOptions.support} onChange={(value) => updateParam("support", value)} /></div>
                <FilterSelect label="Difficulty" value={filters.difficulty ?? "all"} options={[{ value: "all", label: "All difficulties" }, ...unique(data.results, "difficulty").map((value) => ({ value, label: businessLabel(value) }))]} onChange={(value) => updateParam("difficulty", value)} />
                <FilterSelect label="Evidence status" value={filters.evidence ?? "all"} options={[{ value: "all", label: "All evidence" }, ...unique(data.results, "evidence_status").map((value) => ({ value, label: businessLabel(value) }))]} onChange={(value) => updateParam("evidence", value)} />
                <FilterSelect label="Provider" value={filters.provider ?? "all"} options={[{ value: "all", label: "All providers" }, ...unique(data.results, "llm_provider").map((value) => ({ value, label: businessLabel(value) }))]} onChange={(value) => updateParam("provider", value)} />
                <FilterSelect label="Fallback used" value={filters.fallback ?? "all"} options={booleanOptions} onChange={(value) => updateParam("fallback", value)} />
                <FilterSelect label="Numeric mismatch" value={filters.numericMismatch ?? "all"} options={booleanOptions} onChange={(value) => updateParam("numericMismatch", value)} />
                <FilterSelect label="Scope risk" value={filters.scopeRisk ?? "all"} options={booleanOptions} onChange={(value) => updateParam("scopeRisk", value)} />
                <FilterSelect label="Direct support" value={filters.directSupport ?? "all"} options={booleanOptions} onChange={(value) => updateParam("directSupport", value)} />
              </div>
            </PopoverContent>
          </Popover>
        </div>
        <div className="mt-3 text-sm text-neutral-600">Showing <span className="font-metric font-semibold text-neutral-900">{filtered.length}</span> of <span className="font-metric font-semibold text-neutral-900">{data.results.length}</span> cases</div>
      </div>

      <div className="mt-4 hidden rounded-xl border border-neutral-200 bg-white lg:block">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((group) => <TableRow key={group.id}>{group.headers.map((header) => <TableHead key={header.id} className={["category", "difficulty", "provider", "latency"].includes(header.column.id) ? "hidden xl:table-cell" : ""}><button type="button" className="flex items-center gap-1" onClick={header.column.getToggleSortingHandler()}>{flexRender(header.column.columnDef.header, header.getContext())}{header.column.getIsSorted() === "asc" ? " ↑" : header.column.getIsSorted() === "desc" ? " ↓" : ""}</button></TableHead>)}</TableRow>)}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => <TableRow key={row.id}>{row.getVisibleCells().map((cell) => <TableCell key={cell.id} className={`${["category", "difficulty", "provider", "latency"].includes(cell.column.id) ? "hidden xl:table-cell " : ""}whitespace-normal`}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>)}</TableRow>)}
          </TableBody>
        </Table>
        {filtered.length === 0 ? <div className="p-8 text-center text-sm text-neutral-600">No cases match the selected filters.</div> : null}
      </div>

      <div className="mt-4 space-y-3 lg:hidden">
        {filtered.map((item) => { const result = evaluationCasePresentation(item).overall; return <button key={item.id} type="button" onClick={() => openCase(item.id)} className="w-full rounded-xl border border-neutral-200 bg-white p-4 text-left focus-visible:ring-2 focus-visible:ring-teal-700"><div className="flex items-start justify-between gap-3"><span className="font-metric text-xs text-neutral-500">{item.id}</span><StatusPill compact status={result.status} label={result.label} /></div><div className="mt-2 text-sm leading-5 font-medium text-neutral-900">{item.question}</div><div className="mt-3"><DiagnosticPill diagnostic={item.diagnostic} /></div></button>; })}
      </div>

      <CaseDrawer evaluationCase={selected} onOpenChange={(open) => { if (!open) updateParam("case", ""); }} />
    </>
  );
}
