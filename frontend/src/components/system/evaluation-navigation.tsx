"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { evaluationNavigation } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function EvaluationNavigation() {
  const pathname = usePathname();

  return (
    <nav aria-label="Evaluation sections" className="mb-6 overflow-x-auto">
      <div className="flex min-w-max border-b border-neutral-200">
        {evaluationNavigation.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "border-b-2 border-transparent px-4 py-3 text-sm font-medium text-neutral-500 hover:text-neutral-800",
                active && "border-teal-700 text-teal-800",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
