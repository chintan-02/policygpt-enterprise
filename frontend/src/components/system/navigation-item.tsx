"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { NavigationItemDefinition } from "@/lib/navigation";
import { cn } from "@/lib/utils";

type NavigationItemProps = NavigationItemDefinition & {
  onNavigate?: () => void;
};

export function NavigationItem({
  label,
  href,
  icon: Icon,
  matchPrefix,
  onNavigate,
}: NavigationItemProps) {
  const pathname = usePathname();
  const isActive = matchPrefix
    ? pathname.startsWith(matchPrefix)
    : pathname === href;

  return (
    <Link
      href={href}
      onClick={onNavigate}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "group flex min-h-10 items-center gap-3 rounded-lg border border-transparent px-3 py-2 text-sm font-medium text-navy-100 transition-colors hover:bg-white/6 hover:text-white focus-visible:outline-teal-300",
        isActive &&
          "border-teal-600/30 bg-teal-700/25 text-white before:h-5 before:w-0.5 before:rounded-full before:bg-teal-300",
      )}
    >
      <Icon aria-hidden="true" size={18} strokeWidth={1.75} />
      <span>{label}</span>
    </Link>
  );
}
