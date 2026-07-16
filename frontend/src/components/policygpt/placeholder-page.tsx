import type { LucideIcon } from "lucide-react";
import { PageHeader } from "@/components/system/page-header";
import { EmptyState } from "./empty-state";

export function PlaceholderPage({
  title,
  description,
  emptyTitle,
  emptyDescription,
  icon,
}: {
  title: string;
  description: string;
  emptyTitle: string;
  emptyDescription: string;
  icon?: LucideIcon;
}) {
  return (
    <>
      <PageHeader title={title} description={description} />
      <EmptyState title={emptyTitle} description={emptyDescription} icon={icon} />
    </>
  );
}
