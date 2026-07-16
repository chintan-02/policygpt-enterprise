import { StatusPill } from "@/components/policygpt/status-pill";
import {
  documentStatusLabels,
  documentStatusTones,
  type DocumentStatus,
} from "@/lib/domain/document";

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <StatusPill
      compact
      status={documentStatusTones[status]}
      label={documentStatusLabels[status]}
    />
  );
}
