import { describe, expect, it } from "vitest";
import { backendReadinessSchema } from "./readiness";

const readyPayload = {
  status: "ready",
  checks: {
    database: { status: "ready" },
    vector_store: { status: "ready" },
  },
  answer_generation: {
    status: "citation_only_fallback",
    provider: "groq",
  },
};

describe("backend readiness validation", () => {
  it("accepts ready and dependency-unavailable responses", () => {
    expect(backendReadinessSchema.safeParse(readyPayload).success).toBe(true);
    expect(
      backendReadinessSchema.safeParse({
        ...readyPayload,
        status: "not_ready",
        checks: {
          database: { status: "unavailable" },
          vector_store: { status: "ready" },
        },
      }).success,
    ).toBe(true);
  });

  it("rejects internal fields and unsafe unknown states by stripping them", () => {
    const result = backendReadinessSchema.parse({
      ...readyPayload,
      database_url: "postgresql://secret@internal-db/policygpt",
      checks: {
        ...readyPayload.checks,
        database: { status: "ready", host: "internal-db" },
      },
    });
    expect(JSON.stringify(result)).not.toContain("internal-db");
    expect(
      backendReadinessSchema.safeParse({
        ...readyPayload,
        checks: { ...readyPayload.checks, database: { status: "mystery" } },
      }).success,
    ).toBe(false);
  });
});
