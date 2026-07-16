import type {
  FrontendHealthResponse,
  FrontendReadinessResponse,
  HealthStatus,
} from "@/lib/api/types";

export type SystemOperationalState = {
  status: HealthStatus;
  title: string;
  message: string;
};

export function deriveSystemOperationalState(
  health: FrontendHealthResponse,
  readiness: FrontendReadinessResponse,
): SystemOperationalState {
  if (!health.backendReachable || readiness.status === "unavailable") {
    return {
      status: "unavailable",
      title: "Backend unavailable",
      message: "Required service readiness could not be verified.",
    };
  }

  if (health.status === "degraded") {
    return {
      status: "degraded",
      title: "Backend liveness degraded",
      message: "The backend responded, but its process state was not operational.",
    };
  }

  if (
    readiness.status === "not_ready" ||
    readiness.database !== "ready" ||
    readiness.vectorStore !== "ready"
  ) {
    return {
      status: "unavailable",
      title: "Evidence services unavailable",
      message: "A required metadata or retrieval dependency is unavailable.",
    };
  }

  if (
    readiness.provider === "citation_only_fallback" ||
    readiness.provider === "unavailable" ||
    readiness.provider === "unknown"
  ) {
    return {
      status: "degraded",
      title: "Citation-only fallback active",
      message:
        "Core evidence services are ready, but generated answers are unavailable. Citation-only fallback remains active.",
    };
  }

  return {
    status: "operational",
    title: "All required evidence services are ready",
    message: "Metadata, evidence retrieval, and configured answer generation are available.",
  };
}

export function dependencyPresentation(status: "ready" | "unavailable" | "unknown") {
  if (status === "ready") {
    return { status: "operational" as const, label: "Ready" };
  }
  if (status === "unavailable") {
    return { status: "unavailable" as const, label: "Unavailable" };
  }
  return { status: "degraded" as const, label: "Unknown" };
}

export function providerPresentation(status: FrontendReadinessResponse["provider"]) {
  if (status === "configured") {
    return { status: "operational" as const, label: "Configured" };
  }
  if (status === "citation_only_fallback") {
    return { status: "degraded" as const, label: "Citation-only fallback" };
  }
  if (status === "unavailable") {
    return { status: "degraded" as const, label: "Unavailable" };
  }
  return { status: "degraded" as const, label: "Unknown" };
}
