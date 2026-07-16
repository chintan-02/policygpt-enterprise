from typing import NoReturn

from fastapi import APIRouter, Depends, Response, status

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.schemas.evaluation import EvaluationArtifactResponse
from app.services.evaluation_results_service import (
    EvaluationArtifactInvalidError,
    EvaluationArtifactNotFoundError,
    EvaluationResultsService,
)


router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


def get_evaluation_results_service() -> EvaluationResultsService:
    settings = get_settings()
    try:
        return EvaluationResultsService(settings.evaluation_results_path)
    except EvaluationArtifactInvalidError as exc:
        raise AppException(
            message="The evaluation result could not be validated.",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code="EVALUATION_INVALID",
        ) from exc


def _raise_safe_artifact_error(exc: Exception) -> NoReturn:
    if isinstance(exc, EvaluationArtifactNotFoundError):
        raise AppException(
            message="No evaluation result is available.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="EVALUATION_NOT_FOUND",
        ) from exc
    raise AppException(
        message="The evaluation result could not be validated.",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error_code="EVALUATION_INVALID",
    ) from exc


@router.get(
    "/latest",
    response_model=EvaluationArtifactResponse,
    summary="Read the latest evaluation artifact",
)
def get_latest_evaluation(
    service: EvaluationResultsService = Depends(get_evaluation_results_service),
) -> EvaluationArtifactResponse:
    try:
        return service.load_latest()
    except (EvaluationArtifactNotFoundError, EvaluationArtifactInvalidError) as exc:
        _raise_safe_artifact_error(exc)


@router.get(
    "/latest.csv",
    response_class=Response,
    summary="Download the latest evaluation cases as CSV",
)
def download_latest_evaluation_csv(
    service: EvaluationResultsService = Depends(get_evaluation_results_service),
) -> Response:
    try:
        content = service.read_latest_csv()
    except (EvaluationArtifactNotFoundError, EvaluationArtifactInvalidError) as exc:
        _raise_safe_artifact_error(exc)

    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": (
                'attachment; filename="policygpt-latest-evaluation.csv"'
            ),
        },
    )
