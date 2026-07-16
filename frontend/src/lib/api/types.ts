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
  app?: {
    name?: unknown;
    environment?: unknown;
  };
};
