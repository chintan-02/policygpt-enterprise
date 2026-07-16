import { beforeEach, describe, expect, it, vi } from "vitest";

const { getBackendReadiness } = vi.hoisted(() => ({
  getBackendReadiness: vi.fn(),
}));
vi.mock("@/lib/api/readiness", () => ({ getBackendReadiness }));

import { GET } from "./route";

const ready = {
  status: "ready" as const,
  database: "ready" as const,
  vectorStore: "ready" as const,
  provider: "configured" as const,
  providerName: "groq" as const,
  message: "Ready.",
  checkedAt: "2026-07-16T12:00:00Z",
  requestId: "backend-trace-123",
};

describe("readiness BFF route", () => {
  beforeEach(() => getBackendReadiness.mockReset());

  it("forwards a safe request ID and disables caching", async () => {
    getBackendReadiness.mockResolvedValue(ready);
    const response = await GET(
      new Request("http://localhost/api/ready", {
        headers: { "X-Request-ID": "portfolio-demo-123" },
      }),
    );
    expect(getBackendReadiness).toHaveBeenCalledWith("portfolio-demo-123");
    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(response.headers.get("x-request-id")).toBe("backend-trace-123");
  });

  it("normalizes backend unavailability without exposing internal hosts", async () => {
    getBackendReadiness.mockResolvedValue({
      ...ready,
      status: "unavailable",
      database: "unknown",
      vectorStore: "unknown",
      provider: "unknown",
      providerName: undefined,
      requestId: undefined,
      message: "Backend readiness could not be checked.",
    });
    const response = await GET(new Request("http://localhost/api/ready"));
    const body = await response.text();
    expect(response.status).toBe(503);
    expect(body).not.toContain("FASTAPI_URL");
    expect(body).not.toContain("backend:8000");
    expect(body).not.toContain("password");
  });

  it("does not forward unsafe inbound request IDs", async () => {
    getBackendReadiness.mockResolvedValue(ready);
    await GET(
      new Request("http://localhost/api/ready", {
        headers: { "X-Request-ID": "x".repeat(129) },
      }),
    );
    expect(getBackendReadiness).toHaveBeenCalledWith(undefined);
  });
});
