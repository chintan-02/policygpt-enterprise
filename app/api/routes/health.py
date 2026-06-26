from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check() -> dict:
    """
    Basic health check endpoint.

    Used to confirm that the FastAPI backend is running.
    """

    settings = get_settings()

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }