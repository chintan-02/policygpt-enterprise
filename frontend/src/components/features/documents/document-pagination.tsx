import { Button } from "@/components/ui/button";
import {
  documentResultRange,
  nextDocumentOffset,
  previousDocumentOffset,
} from "@/lib/domain/document";
import type { ParsedDocumentList } from "@/lib/validation/document";

export function DocumentPagination({
  data,
  onOffset,
}: {
  data: ParsedDocumentList;
  onOffset: (offset: number) => void;
}) {
  const previous = previousDocumentOffset(data);
  const next = nextDocumentOffset(data);
  return (
    <nav className="flex flex-col gap-3 border-t border-neutral-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between" aria-label="Document registry pagination">
      <p className="font-metric text-xs text-neutral-600" aria-live="polite">{documentResultRange(data)}</p>
      <div className="flex gap-2">
        <Button variant="outline" disabled={previous === null} onClick={() => previous !== null && onOffset(previous)}>Previous</Button>
        <Button variant="outline" disabled={next === null} onClick={() => next !== null && onOffset(next)}>Next</Button>
      </div>
    </nav>
  );
}
