import { AppShell } from "@/components/system/app-shell";
import { getBackendHealth } from "@/lib/api/health";
import { getPublicAppEnvironment } from "@/lib/environment";

// Console routes depend on live FastAPI state and must never be prerendered
// during a release image build, when the backend is intentionally unavailable.
export const dynamic = "force-dynamic";

export default async function ConsoleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [health, app] = await Promise.all([
    getBackendHealth(),
    Promise.resolve(getPublicAppEnvironment()),
  ]);

  return (
    <AppShell health={health} app={app}>
      {children}
    </AppShell>
  );
}
