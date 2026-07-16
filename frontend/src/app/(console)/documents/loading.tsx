import { Skeleton } from "@/components/ui/skeleton";

export default function DocumentsLoading() {
  return <div aria-label="Loading document registry" aria-busy="true"><div className="flex items-start justify-between gap-4"><div className="space-y-3"><Skeleton className="h-8 w-44" /><Skeleton className="h-4 w-80 max-w-full" /></div><Skeleton className="h-9 w-32" /></div><div className="mt-6 grid gap-3 sm:grid-cols-3">{Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} className="h-16 rounded-xl" />)}</div><Skeleton className="mt-5 h-24 rounded-xl" /><Skeleton className="mt-4 h-80 rounded-xl" /></div>;
}
