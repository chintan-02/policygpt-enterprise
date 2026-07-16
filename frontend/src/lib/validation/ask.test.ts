import { describe, expect, it } from "vitest";
import { askRequestSchema, MAX_QUESTION_LENGTH } from "./ask";

describe("askRequestSchema", () => {
  it("trims and accepts a policy question", () => {
    expect(askRequestSchema.parse({ question: "  What is the leave policy?  " })).toEqual({
      question: "What is the leave policy?",
    });
  });

  it("rejects an empty question", () => {
    expect(askRequestSchema.safeParse({ question: "" }).success).toBe(false);
  });

  it("rejects a whitespace-only question", () => {
    expect(askRequestSchema.safeParse({ question: "   " }).success).toBe(false);
  });

  it("rejects a question above the maximum length", () => {
    expect(
      askRequestSchema.safeParse({ question: "x".repeat(MAX_QUESTION_LENGTH + 1) }).success,
    ).toBe(false);
  });

  it("accepts a question at the maximum length", () => {
    expect(
      askRequestSchema.safeParse({ question: "x".repeat(MAX_QUESTION_LENGTH) }).success,
    ).toBe(true);
  });
});
