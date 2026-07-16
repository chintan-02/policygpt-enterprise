import { z } from "zod";

export const MAX_QUESTION_LENGTH = 2000;

export const askRequestSchema = z.object({
  question: z
    .string()
    .trim()
    .min(1, "Enter a policy question.")
    .max(
      MAX_QUESTION_LENGTH,
      `Keep the question to ${MAX_QUESTION_LENGTH.toLocaleString()} characters or fewer.`,
    ),
});

export type AskRequestInput = z.input<typeof askRequestSchema>;
export type AskRequest = z.output<typeof askRequestSchema>;
