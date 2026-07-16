from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.routes.documents import router as documents_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, request_id_from_scope

configure_logging()

settings = get_settings()
logger = structlog.get_logger(__name__)

OPENAPI_TAGS = [
    {
        "name": "Operations",
        "description": "Lightweight liveness and dependency-aware readiness checks.",
    },
    {
        "name": "Documents",
        "description": "PDF ingestion, metadata lifecycle, retrieval, evidence, and Ask workflows.",
    },
    {
        "name": "Evaluations",
        "description": "Read-only access to the latest validated RAG evaluation artifact.",
    },
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="PolicyGPT Enterprise Evidence API",
        version=settings.app_version,
        description=(
            "Evidence-first policy intelligence API for durable PDF ingestion, "
            "metadata-aware retrieval, page-level citations, calibrated confidence, "
            "and provider-safe answer fallback."
        ),
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=OPENAPI_TAGS,
        contact={"name": "PolicyGPT Enterprise project maintainers"},
        license_info={"name": "Portfolio demonstration — no commercial license granted"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    register_routes(app)

    @app.get("/")
    def root() -> dict:
        return {
            "message": "PolicyGPT Enterprise backend is running.",
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
            "readiness": f"{settings.api_prefix}/ready",
            "upload": f"{settings.api_prefix}/documents/upload",
        }

    return app


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)
    app.include_router(evaluations_router, prefix=settings.api_prefix)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        logger.warning(
            "application_exception",
            route=request.scope.get("route").path if request.scope.get("route") else request.url.path,
            error_code=exc.error_code,
            status_code=exc.status_code,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        safe_errors = [
            {
                "type": error.get("type", "validation_error"),
                "loc": list(error.get("loc", ())),
                "msg": error.get("msg", "Invalid value."),
            }
            for error in exc.errors()
        ]
        logger.warning(
            "request_validation_error",
            route=request.scope.get("route").path if request.scope.get("route") else request.url.path,
            validation_error_count=len(safe_errors),
        )

        request_id = request_id_from_scope(request.scope)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "request_id": request_id,
                    "details": safe_errors,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            route=request.scope.get("route").path if request.scope.get("route") else request.url.path,
            error_type=type(exc).__name__,
        )

        request_id = request_id_from_scope(request.scope)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "request_id": request_id,
                },
            },
        )


app = create_app()
