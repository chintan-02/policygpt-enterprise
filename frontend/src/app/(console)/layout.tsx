import { AppShell } from "@/components/system/app-shell";
import { getBackendHealth } from "@/lib/api/health";
import { getPublicAppEnvironment } from "@/lib/environment";

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
