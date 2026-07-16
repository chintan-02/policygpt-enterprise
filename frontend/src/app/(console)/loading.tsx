import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div aria-label="Loading page" aria-busy="true">
      <div className="mb-6 space-y-3">
        <Skeleton className="h-8 w-44" />
        <Skeleton className="h-4 w-full max-w-lg" />
      </div>
      <div className="grid gap-[22px] sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="rounded-xl border border-neutral-200 bg-white p-5">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="mt-5 h-8 w-36" />
            <Skeleton className="mt-4 h-4 w-full" />
            <Skeleton className="mt-2 h-4 w-4/5" />
          </div>
        ))}
      </div>
      <div className="mt-[22px] rounded-xl border border-neutral-200 bg-white p-5">
        <Skeleton className="h-5 w-36" />
        <Skeleton className="mt-4 h-4 w-full max-w-3xl" />
        <Skeleton className="mt-2 h-4 w-2/3" />
      </div>
    </div>
  );
}
