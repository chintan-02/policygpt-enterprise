import { getBackendHealth } from "@/lib/api/health";

export async function GET() {
  const health = await getBackendHealth();

  return Response.json(health, {
    status: health.backendReachable ? 200 : 503,
    headers: { "Cache-Control": "no-store" },
  });
}
