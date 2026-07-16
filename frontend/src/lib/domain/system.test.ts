import { describe, expect, it } from "vitest";
import type { FrontendHealthResponse, FrontendReadinessResponse } from "@/lib/api/types";
import {
  dependencyPresentation,
  deriveSystemOperationalState,
  providerPresentation,
} from "./system";

const health: FrontendHealthResponse = {
  status: "operational",
  backendReachable: true,
  serviceName: "PolicyGPT Enterprise",
  message: "Backend is live.",
};

const readiness: FrontendReadinessResponse = {
  status: "ready",
  database: "ready",
  vectorStore: "ready",
  provider: "configured",
  providerName: "groq",
  message: "Ready.",
  checkedAt: "2026-07-16T12:00:00Z",
};

describe("System operational state", () => {
  it("maps fully ready dependencies to operational", () => {
    expect(deriveSystemOperationalState(health, readiness).status).toBe("operational");
  });

  it.each(["citation_only_fallback", "unavailable", "unknown"] as const)(
    "maps provider state %s to degraded while evidence stays ready",
    (provider) => {
      const state = deriveSystemOperationalState(health, { ...readiness, provider });
      expect(state.status).toBe("degraded");
      expect(state.message).toBe(
        "Core evidence services are ready, but generated answers are unavailable. Citation-only fallback remains active.",
      );
      expect(dependencyPresentation(readiness.database)).toEqual({
        status: "operational",
        label: "Ready",
      });
      expect(dependencyPresentation(readiness.vectorStore)).toEqual({
        status: "operational",
        label: "Ready",
      });
    },
  );

  it.each(["database", "vectorStore"] as const)(
    "maps %s outage to unavailable",
    (dependency) => {
      const state = deriveSystemOperationalState(health, {
        ...readiness,
        status: "not_ready",
        [dependency]: "unavailable",
      });
      expect(state.status).toBe("unavailable");
      expect(state.message).toContain("required");
    },
  );

  it("handles backend and unknown dependency states safely", () => {
    expect(
      deriveSystemOperationalState(
        { ...health, status: "unavailable", backendReachable: false },
        { ...readiness, status: "unavailable" },
      ).status,
    ).toBe("unavailable");
    expect(
      deriveSystemOperationalState(health, { ...readiness, database: "unknown" }).status,
    ).toBe("unavailable");
    expect(dependencyPresentation("unknown").label).toBe("Unknown");
    expect(providerPresentation("citation_only_fallback").label).toContain("Citation-only");
  });

  it("keeps request IDs as diagnostics, not status inputs", () => {
    const withoutId = deriveSystemOperationalState(health, readiness);
    const withId = deriveSystemOperationalState(health, {
      ...readiness,
      requestId: "diagnostic-123",
    });
    expect(withId).toEqual(withoutId);
  });
});
