import type { FrontendHealthResponse, HealthStatus } from "@/lib/api/types";
import type { PublicAppEnvironment } from "@/lib/environment";
import { AppSidebar } from "./app-sidebar";
import { Topbar } from "./topbar";

export function AppShell({
  children,
  health,
  app,
  platformStatus,
}: {
  children: React.ReactNode;
  health: FrontendHealthResponse;
  app: PublicAppEnvironment;
  platformStatus: HealthStatus;
}) {
  return (
    <div className="min-h-dvh bg-background">
      <a
        href="#main-content"
        className="fixed top-3 left-3 z-[100] -translate-y-20 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-teal-800 shadow-sm transition-transform focus:translate-y-0 xl:left-[264px]"
      >
        Skip to content
      </a>
      <AppSidebar health={health} app={app} />
      <div className="min-w-0 xl:ml-[248px]">
        <Topbar health={health} app={app} platformStatus={platformStatus} />
        <main id="main-content" className="min-w-0">
          <div className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-7 lg:py-7">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
