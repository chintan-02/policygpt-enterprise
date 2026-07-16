import { Skeleton } from "@/components/ui/skeleton";

export default function AskLoading() {
  return (
    <div aria-label="Loading Ask PolicyGPT">
      <Skeleton className="h-8 w-52" />
      <Skeleton className="mt-3 h-5 w-full max-w-xl" />
      <div className="mt-8 rounded-xl border border-neutral-200 bg-white p-5">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="mt-4 h-32 w-full" />
        <Skeleton className="mt-4 h-9 w-36" />
      </div>
      <div className="mt-[22px] grid gap-[22px] lg:grid-cols-[minmax(0,3fr)_minmax(340px,2fr)]">
        <Skeleton className="h-56 w-full" />
        <Skeleton className="h-56 w-full" />
      </div>
    </div>
  );
}
