import type { FrontendHealthResponse } from "@/lib/api/types";
import type { PublicAppEnvironment } from "@/lib/environment";
import { StatusPill } from "@/components/policygpt/status-pill";
import { CurrentPageContext } from "./current-page-context";
import { MobileSidebar } from "./mobile-sidebar";

export function Topbar({
  health,
  app,
}: {
  health: FrontendHealthResponse;
  app: PublicAppEnvironment;
}) {
  return (
    <header className="sticky top-0 z-20 h-16 border-b border-neutral-200 bg-white/95">
      <div className="flex h-full items-center justify-between gap-4 px-4 sm:px-6 lg:px-7">
        <div className="flex min-w-0 items-center gap-3">
          <div className="xl:hidden">
            <MobileSidebar health={health} app={app} />
          </div>
          <div className="min-w-0">
            <CurrentPageContext />
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <StatusPill status={health.status} />
          <span className="hidden rounded-lg border border-neutral-200 bg-neutral-50 px-2.5 py-1 text-xs font-medium text-neutral-600 sm:inline-flex">
            {app.appEnvironment}
          </span>
        </div>
      </div>
    </header>
  );
}
