"use client";

import { ChevronDown, FileSearch } from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";
import { EngineeringPanel } from "@/components/policygpt/engineering-panel";
import { ProvenanceRail } from "@/components/policygpt/provenance-rail";
import { Button } from "@/components/ui/button";
import type { AskResult } from "@/lib/domain/ask";
import {
  expandedCitationForRequest,
  selectCitationForRequest,
  type CitationExpansionState,
} from "@/lib/domain/ask-presentation";
import { cn } from "@/lib/utils";

function RawMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt>{label}</dt>
      <dd className="font-metric text-neutral-700">{value.toFixed(4)}</dd>
    </div>
  );
}

function sourceRole(index: number): string {
  if (index === 0) return "Primary evidence";
  if (index === 1) return "Supporting evidence";
  return "Additional context";
}

export function EvidencePanel({
  result,
  requestSequence,
}: {
  result: AskResult | null;
  requestSequence: number;
}) {
  const evidenceContainerRef = useRef<HTMLDivElement>(null);
  const [citationExpansion, setCitationExpansion] =
    useState<CitationExpansionState>({
      requestSequence,
      expandedCitationId: null,
    });
  const expandedCitationId = expandedCitationForRequest(
    citationExpansion,
    requestSequence,
  );

  useLayoutEffect(() => {
    evidenceContainerRef.current?.scrollTo({
      top: 0,
      behavior: "auto",
    });
  }, [requestSequence, result]);

  if (!result || result.citations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-neutral-300 bg-white p-6 text-center">
        <FileSearch aria-hidden="true" className="text-neutral-400" size={24} strokeWidth={1.6} />
        <h2 className="mt-3 text-sm font-semibold text-neutral-800">Evidence appears here</h2>
        <p className="mt-1 max-w-xs text-sm leading-5 text-neutral-600">
          Source excerpts are shown only when the backend returns citation-backed evidence.
        </p>
      </div>
    );
  }

  return (
    <aside
      className="min-w-0 xl:sticky xl:top-[86px] xl:flex xl:max-h-[calc(100dvh-110px)] xl:flex-col"
      aria-labelledby="evidence-heading"
    >
      <div className="shrink-0 pb-3">
        <h2 id="evidence-heading" className="text-base font-semibold text-neutral-900">
          Source evidence
        </h2>
        <p className="mt-1 text-sm leading-5 text-neutral-600">
          Review the {result.citations.length} cited policy {result.citations.length === 1 ? "passage" : "passages"}.
        </p>
      </div>

      <div
        ref={evidenceContainerRef}
        className="evidence-scrollbar space-y-3 xl:min-h-0 xl:overflow-y-auto xl:pr-2"
      >
        {result.citations.map((citation, index) => {
          const expanded = expandedCitationId === citation.id;
          const excerptId = `citation-excerpt-${index + 1}`;

          return (
            <article key={citation.id} className="rounded-xl border border-neutral-200 bg-white p-4">
              <div className="mb-2.5 text-xs font-semibold text-neutral-600">
                Source {index + 1} <span aria-hidden="true">—</span> {sourceRole(index)}
              </div>
              <ProvenanceRail
                document={citation.document}
                page={citation.page}
                section={citation.section}
                support={`${citation.support} support`}
                mode="detailed"
              />
              <blockquote
                id={excerptId}
                className={cn(
                  "mt-3 border-l-2 border-neutral-200 pl-3 text-sm leading-6 text-neutral-700",
                  !expanded && "line-clamp-4",
                )}
              >
                {citation.excerpt}
              </blockquote>
              <Button
                type="button"
                variant="link"
                size="sm"
                className="mt-2 h-auto px-0 py-1"
                aria-expanded={expanded}
                aria-controls={excerptId}
                onClick={() =>
                  setCitationExpansion((current) =>
                    selectCitationForRequest(
                      current,
                      requestSequence,
                      citation.id,
                    ),
                  )
                }
              >
                {expanded ? "Collapse excerpt" : "View complete excerpt"}
                <ChevronDown
                  aria-hidden="true"
                  className={cn("transition-transform", expanded && "rotate-180")}
                />
              </Button>
            </article>
          );
        })}

        <EngineeringPanel title="Evidence engineering details">
          <dl className="space-y-2 text-xs">
            {result.citations.map((citation, index) => (
              <RawMetric
                key={citation.id}
                label={`Source ${index + 1} retrieval`}
                value={citation.retrievalScore}
              />
            ))}
          </dl>
        </EngineeringPanel>
      </div>
    </aside>
  );
}
