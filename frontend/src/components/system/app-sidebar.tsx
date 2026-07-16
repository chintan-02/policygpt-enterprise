"use client";

import type { FrontendHealthResponse } from "@/lib/api/types";
import type { PublicAppEnvironment } from "@/lib/environment";
import { navigationGroups } from "@/lib/navigation";
import { StatusPill } from "@/components/policygpt/status-pill";
import { NavigationItem } from "./navigation-item";

type AppSidebarProps = {
  health: FrontendHealthResponse;
  app: PublicAppEnvironment;
  onNavigate?: () => void;
  mobile?: boolean;
};

export function AppSidebar({
  health,
  app,
  onNavigate,
  mobile = false,
}: AppSidebarProps) {
  return (
    <aside
      aria-label="Primary navigation"
      className={
        mobile
          ? "flex min-h-0 flex-1 flex-col bg-navy-800"
          : "fixed inset-y-0 left-0 z-30 hidden w-[248px] flex-col bg-navy-800 xl:flex"
      }
    >
      <div className="flex h-20 shrink-0 items-center border-b border-white/10 px-6">
        <div>
          <div className="text-[13px] font-semibold tracking-[0.17em] text-white">
            POLICYGPT
          </div>
          <div className="mt-1 text-xs text-navy-200">Evidence Intelligence</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-5">
        <div className="space-y-6">
          {navigationGroups.map((group) => (
            <div key={group.label}>
              <div className="mb-2 px-3 text-[11px] font-semibold tracking-[0.14em] text-navy-200 uppercase">
                {group.label}
              </div>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavigationItem
                    key={item.href}
                    {...item}
                    onNavigate={onNavigate}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </nav>

      <div className="shrink-0 border-t border-white/10 px-5 py-5 text-xs text-navy-200">
        <dl className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <dt>Backend</dt>
            <dd>
              <StatusPill status={health.status} compact inverse />
            </dd>
          </div>
          <div className="flex items-center justify-between gap-3">
            <dt>Environment</dt>
            <dd className="font-metric font-medium text-white">{app.appEnvironment}</dd>
          </div>
          <div className="flex items-center justify-between gap-3">
            <dt>Version</dt>
            <dd className="font-metric font-medium text-white">{app.appVersion}</dd>
          </div>
        </dl>
      </div>
    </aside>
  );
}
