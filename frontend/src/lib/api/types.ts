export type HealthStatus = "operational" | "degraded" | "unavailable";

export type FrontendHealthResponse = {
  status: HealthStatus;
  backendReachable: boolean;
  serviceName: string;
  environment?: string;
  message: string;
};

export type BackendHealthPayload = {
  status?: unknown;
  service?: unknown;
  version?: unknown;
  environment?: unknown;
};

export type DependencyStatus = "ready" | "unavailable" | "unknown";
export type ProviderStatus =
  | "configured"
  | "citation_only_fallback"
  | "unavailable"
  | "unknown";

export type FrontendReadinessResponse = {
  status: "ready" | "not_ready" | "unavailable";
  database: DependencyStatus;
  vectorStore: DependencyStatus;
  provider: ProviderStatus;
  providerName?: "groq" | "openai" | "none";
  message: string;
  checkedAt: string;
  requestId?: string;
};
