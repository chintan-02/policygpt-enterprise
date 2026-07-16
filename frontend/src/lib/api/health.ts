import "server-only";

import { fetchFromBackend } from "@/lib/api/client";
import type {
  BackendHealthPayload,
  FrontendHealthResponse,
} from "@/lib/api/types";
import { ServerEnvironmentError } from "@/lib/environment";

const DEFAULT_SERVICE_NAME = "PolicyGPT Enterprise";

function safeText(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

export async function getBackendHealth(): Promise<FrontendHealthResponse> {
  try {
    const response = await fetchFromBackend("/api/v1/health");

    if (!response.ok) {
      return {
        status: "degraded",
        backendReachable: true,
        serviceName: DEFAULT_SERVICE_NAME,
        message: "The backend responded, but its health check did not complete successfully.",
      };
    }

    const payload = (await response.json()) as BackendHealthPayload;
    const backendStatus = safeText(payload.status)?.toLowerCase();
    const serviceName = safeText(payload.app?.name) ?? DEFAULT_SERVICE_NAME;
    const environment = safeText(payload.app?.environment);

    if (["healthy", "ok", "operational"].includes(backendStatus ?? "")) {
      return {
        status: "operational",
        backendReachable: true,
        serviceName,
        environment,
        message: "The FastAPI evidence pipeline is reachable.",
      };
    }

    return {
      status: "degraded",
      backendReachable: true,
      serviceName,
      environment,
      message: "The backend is reachable, but it reported a non-operational state.",
    };
  } catch (error) {
    if (error instanceof ServerEnvironmentError) {
      throw error;
    }

    return {
      status: "unavailable",
      backendReachable: false,
      serviceName: DEFAULT_SERVICE_NAME,
      message: "The FastAPI backend could not be reached.",
    };
  }
}
