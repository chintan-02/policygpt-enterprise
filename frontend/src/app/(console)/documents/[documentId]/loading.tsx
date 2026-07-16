import { Skeleton } from "@/components/ui/skeleton";

export default function DocumentDetailLoading() {
  return <div aria-label="Loading document metadata" aria-busy="true"><Skeleton className="h-4 w-32" /><Skeleton className="mt-4 h-9 w-72 max-w-full" /><div className="mt-6 grid gap-5 xl:grid-cols-2"><Skeleton className="h-96 rounded-xl" /><Skeleton className="h-72 rounded-xl" /></div><Skeleton className="mt-5 h-64 rounded-xl" /></div>;
}
