import { z } from "zod";

const dependencyCheckSchema = z.object({
  status: z.enum(["ready", "unavailable"]),
});

export const backendReadinessSchema = z.object({
  status: z.enum(["ready", "not_ready"]),
  checks: z.object({
    database: dependencyCheckSchema,
    vector_store: dependencyCheckSchema,
  }),
  answer_generation: z.object({
    status: z.enum(["configured", "citation_only_fallback"]),
    provider: z.enum(["groq", "openai", "none"]),
  }),
});

export type BackendReadiness = z.infer<typeof backendReadinessSchema>;
