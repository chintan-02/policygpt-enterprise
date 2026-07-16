import { AskWorkspaceProvider } from "@/components/ask/ask-workspace-provider";
import { AppShell } from "@/components/system/app-shell";
import { getBackendHealth } from "@/lib/api/health";
import { getBackendReadiness } from "@/lib/api/readiness";
import { deriveSystemOperationalState } from "@/lib/domain/system";
import { getPublicAppEnvironment } from "@/lib/environment";

// Console routes depend on live FastAPI state and must never be prerendered
// during a release image build, when the backend is intentionally unavailable.
export const dynamic = "force-dynamic";

export default async function ConsoleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [health, readiness, app] = await Promise.all([
    getBackendHealth(),
    getBackendReadiness(),
    Promise.resolve(getPublicAppEnvironment()),
  ]);
  const platformStatus = deriveSystemOperationalState(health, readiness).status;

  return (
    <AskWorkspaceProvider>
      <AppShell health={health} app={app} platformStatus={platformStatus}>
        {children}
      </AppShell>
    </AskWorkspaceProvider>
  );
}
