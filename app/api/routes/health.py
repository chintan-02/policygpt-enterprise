from fastapi import APIRouter, Depends, Response, status

from app.core.config import get_settings
from app.schemas.health import LivenessResponse, ReadinessResponse
from app.services.readiness_service import ReadinessService


router = APIRouter(tags=["Operations"])


def get_readiness_service() -> ReadinessService:
    return ReadinessService()


@router.get(
    "/health",
    response_model=LivenessResponse,
    summary="Check process liveness",
    description=(
        "Lightweight process check. It does not contact PostgreSQL, ChromaDB, "
        "embedding models, or answer-generation providers."
    ),
)
def health_check() -> LivenessResponse:
    settings = get_settings()
    return LivenessResponse(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Check deployment readiness",
    description=(
        "Read-only PostgreSQL and ChromaDB accessibility checks. LLM providers "
        "are informational and never gate readiness."
    ),
    responses={503: {"model": ReadinessResponse, "description": "Required dependency unavailable"}},
)
def readiness_check(
    response: Response,
    service: ReadinessService = Depends(get_readiness_service),
) -> ReadinessResponse:
    result = service.check()
    if result.status == "not_ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
