import "server-only";

import { fetchFromBackend } from "@/lib/api/client";
import {
  adaptEvaluationArtifact,
  type EvaluationViewModel,
} from "@/lib/domain/evaluation";
import { ServerEnvironmentError } from "@/lib/environment";

const EVALUATION_TIMEOUT_MS = 5_000;

export type EvaluationApiErrorCode =
  | "EVALUATION_NOT_FOUND"
  | "EVALUATION_INVALID"
  | "BACKEND_UNAVAILABLE"
  | "REQUEST_TIMEOUT"
  | "INVALID_UPSTREAM_RESPONSE";

export class EvaluationApiError extends Error {
  constructor(
    public readonly code: EvaluationApiErrorCode,
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "EvaluationApiError";
  }
}

export function mapEvaluationUpstreamStatus(status: number): EvaluationApiError {
  if (status === 404) {
    return new EvaluationApiError(
      "EVALUATION_NOT_FOUND",
      "No evaluation result is available.",
      404,
    );
  }
  if (status === 422) {
    return new EvaluationApiError(
      "EVALUATION_INVALID",
      "The evaluation result could not be validated.",
      422,
    );
  }
  return new EvaluationApiError(
    "BACKEND_UNAVAILABLE",
    "The evaluation service is unavailable.",
    502,
  );
}

export function mapEvaluationFetchError(error: unknown): EvaluationApiError {
  if (error instanceof EvaluationApiError) return error;
  if (error instanceof DOMException && error.name === "TimeoutError") {
    return new EvaluationApiError(
      "REQUEST_TIMEOUT",
      "The evaluation request timed out.",
      504,
    );
  }
  if (error instanceof ServerEnvironmentError || error instanceof TypeError) {
    return new EvaluationApiError(
      "BACKEND_UNAVAILABLE",
      "The evaluation service is unavailable.",
      502,
    );
  }
  return new EvaluationApiError(
    "INVALID_UPSTREAM_RESPONSE",
    "The evaluation service returned an invalid response.",
    502,
  );
}

export async function getLatestEvaluation(
  signal?: AbortSignal,
): Promise<EvaluationViewModel> {
  try {
    const response = await fetchFromBackend("/api/v1/evaluations/latest", {
      timeoutMs: EVALUATION_TIMEOUT_MS,
      signal,
    });
    if (!response.ok) throw mapEvaluationUpstreamStatus(response.status);
    const payload: unknown = await response.json().catch(() => null);
    try {
      return adaptEvaluationArtifact(payload);
    } catch {
      throw new EvaluationApiError(
        "INVALID_UPSTREAM_RESPONSE",
        "The evaluation service returned an invalid response.",
        502,
      );
    }
  } catch (error) {
    throw mapEvaluationFetchError(error);
  }
}

export async function getLatestEvaluationCsv(
  signal?: AbortSignal,
): Promise<Response> {
  try {
    const response = await fetchFromBackend("/api/v1/evaluations/latest.csv", {
      accept: "text/csv",
      timeoutMs: EVALUATION_TIMEOUT_MS,
      signal,
    });
    if (!response.ok) throw mapEvaluationUpstreamStatus(response.status);
    if (!response.headers.get("content-type")?.toLowerCase().startsWith("text/csv")) {
      throw new EvaluationApiError(
        "INVALID_UPSTREAM_RESPONSE",
        "The evaluation service returned an invalid response.",
        502,
      );
    }
    return response;
  } catch (error) {
    throw mapEvaluationFetchError(error);
  }
}

export type EvaluationPageState =
  | { state: "ready"; data: EvaluationViewModel }
  | {
      state: "error";
      code: EvaluationApiErrorCode;
      title: string;
      message: string;
    };

export async function loadEvaluationPageState(): Promise<EvaluationPageState> {
  try {
    return { state: "ready", data: await getLatestEvaluation() };
  } catch (error) {
    const safeError = mapEvaluationFetchError(error);
    const title =
      safeError.code === "EVALUATION_NOT_FOUND"
        ? "No evaluation result available"
        : safeError.code === "EVALUATION_INVALID"
          ? "The evaluation result could not be validated"
          : "The evaluation service is unavailable";
    return { state: "error", code: safeError.code, title, message: safeError.message };
  }
}
