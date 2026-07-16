import { Skeleton } from "@/components/ui/skeleton";

export default function EvaluationsLoading() {
  return <div aria-label="Loading evaluation data"><Skeleton className="h-8 w-64" /><Skeleton className="mt-3 h-4 w-full max-w-2xl" /><div className="mt-8 grid gap-[22px] sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <Skeleton key={index} className="h-44 rounded-xl" />)}</div></div>;
}
