import "server-only";

import { getFastApiUrl } from "@/lib/environment";

const BACKEND_TIMEOUT_MS = 3000;

export async function fetchFromBackend(
  path: string,
  options?: { accept?: string; timeoutMs?: number; signal?: AbortSignal },
): Promise<Response> {
  const timeoutSignal = AbortSignal.timeout(options?.timeoutMs ?? BACKEND_TIMEOUT_MS);
  return fetch(`${getFastApiUrl()}${path}`, {
    cache: "no-store",
    headers: { Accept: options?.accept ?? "application/json" },
    signal: options?.signal
      ? AbortSignal.any([options.signal, timeoutSignal])
      : timeoutSignal,
  });
}
