"use client";

import Link from "next/link";
import { CircleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <section className="rounded-xl border border-error-200 bg-white px-6 py-12 text-center shadow-xs">
      <div className="mx-auto flex size-10 items-center justify-center rounded-lg bg-error-50 text-error-700">
        <CircleAlert aria-hidden="true" size={20} strokeWidth={1.75} />
      </div>
      <h1 className="mt-4 text-xl font-semibold text-neutral-900">
        This page could not be loaded
      </h1>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-neutral-500">
        A safe retry may resolve the issue. No system details have been exposed.
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Button onClick={() => reset()}>Retry</Button>
        <Button variant="outline" render={<Link href="/" />}>
          Back to Overview
        </Button>
      </div>
    </section>
  );
}
