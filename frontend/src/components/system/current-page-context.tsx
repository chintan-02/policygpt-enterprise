"use client";

import { usePathname } from "next/navigation";
import { pageBreadcrumbs } from "@/lib/navigation";

export function CurrentPageContext() {
  const pathname = usePathname();
  const breadcrumb = pageBreadcrumbs[pathname] ?? {
    section: "PolicyGPT",
    page: "Evidence Intelligence Console",
  };

  return (
    <nav aria-label="Breadcrumb" className="min-w-0">
      <ol className="flex min-w-0 items-center gap-2 text-sm">
        <li className="shrink-0 font-medium text-neutral-500">
          {breadcrumb.section}
        </li>
        <li aria-hidden="true" className="shrink-0 text-neutral-300">
          /
        </li>
        <li
          aria-current="page"
          className="truncate font-semibold text-neutral-800"
        >
          {breadcrumb.page}
        </li>
      </ol>
    </nav>
  );
}
