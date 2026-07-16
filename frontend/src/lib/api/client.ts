import "server-only";

import { getFastApiUrl } from "@/lib/environment";

const BACKEND_TIMEOUT_MS = 3000;

export async function fetchFromBackend(path: string): Promise<Response> {
  return fetch(`${getFastApiUrl()}${path}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
    signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS),
  });
}
