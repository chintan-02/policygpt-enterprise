import {
  EvaluationApiError,
  getLatestEvaluation,
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
    const data = await getLatestEvaluation(request.signal);
    return Response.json(data, {
      headers: {
        "Cache-Control": "no-store",
        "Content-Disposition": 'attachment; filename="policygpt-latest-evaluation.json"',
      },
    });
  } catch (error) {
    return errorResponse(mapEvaluationFetchError(error));
  }
}
