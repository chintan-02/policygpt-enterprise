import "server-only";

import { cache } from "react";
import { fetchFromBackend } from "@/lib/api/client";
import type { FrontendReadinessResponse } from "@/lib/api/types";
import { backendReadinessSchema } from "@/lib/validation/readiness";

const READINESS_TIMEOUT_MS = 3_000;

function safeRequestId(value: string | null): string | undefined {
  return value && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(value)
    ? value
    : undefined;
}

const fetchBackendReadiness = async (
  requestId?: string,
): Promise<FrontendReadinessResponse> => {
  const checkedAt = new Date().toISOString();
  try {
    const response = await fetchFromBackend("/api/v1/ready", {
      timeoutMs: READINESS_TIMEOUT_MS,
      requestId,
    });
    const upstreamRequestId = safeRequestId(response.headers.get("x-request-id"));
    const payload = backendReadinessSchema.safeParse(
      await response.json().catch(() => null),
    );

    if (!payload.success) {
      return {
        status: "unavailable",
        database: "unknown",
        vectorStore: "unknown",
        provider: "unknown",
        message: "The evidence service returned an incomplete readiness response.",
        checkedAt,
        requestId: upstreamRequestId,
      };
    }

    const data = payload.data;
    const requiredReady =
      response.ok &&
      data.status === "ready" &&
      data.checks.database.status === "ready" &&
      data.checks.vector_store.status === "ready";
    return {
      status: requiredReady ? "ready" : "not_ready",
      database: data.checks.database.status,
      vectorStore: data.checks.vector_store.status,
      provider: data.answer_generation.status,
      providerName: data.answer_generation.provider,
      message: requiredReady
        ? "PostgreSQL metadata and Chroma evidence storage are ready."
        : "A required evidence dependency is unavailable.",
      checkedAt,
      requestId: upstreamRequestId,
    };
  } catch {
    return {
      status: "unavailable",
      database: "unknown",
      vectorStore: "unknown",
      provider: "unknown",
      message: "Backend readiness could not be checked.",
      checkedAt,
    };
  }
};

// Layouts and pages can request readiness in the same server render. React's
// request-scoped cache keeps that to one backend readiness check.
export const getBackendReadiness = cache(fetchBackendReadiness);
