import { adaptAskResponse, type AskResult } from "../domain/ask";
import type { AskRequest } from "../validation/ask";

export type AskApiErrorCode =
  | "validation_error"
  | "timeout"
  | "backend_unavailable"
  | "upstream_error"
  | "invalid_response"
  | "request_failed";

export class AskApiError extends Error {
  constructor(
    public readonly code: AskApiErrorCode,
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "AskApiError";
  }
}
type SafeErrorResponse = {
  error?: {
    code?: unknown;
    message?: unknown;
  };
};

function isAskApiErrorCode(value: unknown): value is AskApiErrorCode {
  return [
    "validation_error",
    "timeout",
    "backend_unavailable",
    "upstream_error",
    "invalid_response",
    "request_failed",
  ].includes(String(value));
}

export async function askPolicyQuestion(
  request: AskRequest,
  signal: AbortSignal,
): Promise<AskResult> {
  let response: Response;

  try {
    response = await fetch("/api/ask", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      cache: "no-store",
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new AskApiError(
      "request_failed",
      "The request could not be completed. Check the connection and try again.",
    );
  }

  const payload = (await response.json().catch(() => null)) as SafeErrorResponse | null;

  if (!response.ok) {
    const code = isAskApiErrorCode(payload?.error?.code)
      ? payload.error.code
      : "request_failed";
    const message =
      typeof payload?.error?.message === "string"
        ? payload.error.message
        : "PolicyGPT could not complete the request.";
    throw new AskApiError(code, message, response.status);
  }

  const result = adaptAskResponse(payload);
  if (result.state === "invalid_response") {
    throw new AskApiError(
      "invalid_response",
      "The backend returned an incomplete evidence response. Try again.",
      response.status,
    );
  }
  return result;
}
