import "server-only";

import { getFastApiUrl } from "@/lib/environment";

const BACKEND_TIMEOUT_MS = 3000;

export async function fetchFromBackend(
  path: string,
  options?: {
    accept?: string;
    timeoutMs?: number;
    signal?: AbortSignal;
    requestId?: string;
  },
): Promise<Response> {
  const timeoutSignal = AbortSignal.timeout(options?.timeoutMs ?? BACKEND_TIMEOUT_MS);
  const headers = new Headers({ Accept: options?.accept ?? "application/json" });
  if (options?.requestId && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(options.requestId)) {
    headers.set("X-Request-ID", options.requestId);
  }
  return fetch(`${getFastApiUrl()}${path}`, {
    cache: "no-store",
    headers,
    signal: options?.signal
      ? AbortSignal.any([options.signal, timeoutSignal])
      : timeoutSignal,
  });
}
