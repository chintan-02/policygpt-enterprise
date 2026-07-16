import { getBackendReadiness } from "@/lib/api/readiness";

const SAFE_REQUEST_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;

export async function GET(request: Request) {
  const inboundRequestId = request.headers.get("x-request-id");
  const readiness = await getBackendReadiness(
    inboundRequestId && SAFE_REQUEST_ID.test(inboundRequestId)
      ? inboundRequestId
      : undefined,
  );
  const headers = new Headers({ "Cache-Control": "no-store" });
  if (readiness.requestId) headers.set("X-Request-ID", readiness.requestId);

  return Response.json(readiness, {
    status: readiness.status === "ready" ? 200 : 503,
    headers,
  });
}
