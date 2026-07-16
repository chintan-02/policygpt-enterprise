import {
  EvaluationApiError,
  getLatestEvaluationCsv,
  mapEvaluationFetchError,
} from "@/lib/api/evaluations";

function errorResponse(error: EvaluationApiError) {
  return Response.json(
    { error: { code: error.code, message: error.message } },
    { status: error.status, headers: { "Cache-Control": "no-store" } },
  );
}

export async function GET(request: Request) {
  try {
    const upstream = await getLatestEvaluationCsv(request.signal);
    const disposition = upstream.headers.get("content-disposition");
    const safeDisposition =
      disposition && /^attachment; filename="[a-zA-Z0-9._-]+"$/.test(disposition)
        ? disposition
        : 'attachment; filename="policygpt-latest-evaluation.csv"';
    return new Response(await upstream.arrayBuffer(), {
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": safeDisposition,
      },
    });
  } catch (error) {
    return errorResponse(mapEvaluationFetchError(error));
  }
}
