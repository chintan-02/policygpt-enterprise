import type { components } from "@/lib/api/generated";
import { isGeneratedAskResponse } from "@/lib/domain/ask";
import { getFastApiUrl, ServerEnvironmentError } from "@/lib/environment";
import { askRequestSchema } from "@/lib/validation/ask";

const ASK_TIMEOUT_MS = 60_000;

type GeneratedAskRequest = components["schemas"]["DocumentAnswerRequest"];

function errorResponse(code: string, message: string, status: number) {
  return Response.json(
    { error: { code, message } },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

function requestSignal(request: Request): AbortSignal {
  return AbortSignal.any([
    request.signal,
    AbortSignal.timeout(ASK_TIMEOUT_MS),
  ]);
}

export async function POST(request: Request) {
  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
    return errorResponse(
      "validation_error",
      "Send the policy question as JSON.",
      415,
    );
  }

  const body = await request.json().catch(() => null);
  const parsed = askRequestSchema.safeParse(body);

  if (!parsed.success) {
    return errorResponse(
      "validation_error",
      parsed.error.issues[0]?.message ?? "Enter a valid policy question.",
      400,
    );
  }

  const upstreamBody = {
    question: parsed.data.question,
    top_k: 5,
  } satisfies GeneratedAskRequest;

  try {
    const response = await fetch(`${getFastApiUrl()}/api/v1/documents/ask`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(upstreamBody),
      cache: "no-store",
      signal: requestSignal(request),
    });

    if (!response.ok) {
      const status = response.status >= 500 ? 502 : response.status;
      return errorResponse(
        response.status >= 500 ? "upstream_error" : "validation_error",
        response.status >= 500
          ? "The evidence service could not complete the request."
          : "The evidence service rejected the question.",
        status,
      );
    }

    const payload: unknown = await response.json().catch(() => null);
    if (!isGeneratedAskResponse(payload)) {
      return errorResponse(
        "invalid_response",
        "The evidence service returned an incomplete response.",
        502,
      );
    }

    const headers = new Headers({ "Cache-Control": "no-store" });
    const requestId = response.headers.get("x-request-id");
    if (requestId && /^[a-zA-Z0-9._:-]{1,128}$/.test(requestId)) {
      headers.set("x-request-id", requestId);
    }

    return Response.json(payload, { headers });
  } catch (error) {
    if (error instanceof ServerEnvironmentError) {
      return errorResponse(
        "backend_unavailable",
        "The evidence service is not configured.",
        502,
      );
    }
    if (error instanceof DOMException && error.name === "TimeoutError") {
      return errorResponse(
        "timeout",
        "The evidence request timed out. Try again.",
        504,
      );
    }
    if (request.signal.aborted) {
      return errorResponse("request_failed", "The request was cancelled.", 499);
    }
    if (error instanceof TypeError) {
      return errorResponse(
        "backend_unavailable",
        "The evidence service could not be reached.",
        502,
      );
    }
    return errorResponse(
      "request_failed",
      "PolicyGPT could not complete the request.",
      500,
    );
  }
}
