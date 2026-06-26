from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging

configure_logging()

settings = get_settings()
logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    register_routes(app)

    @app.get("/")
    def root() -> dict:
        return {
            "message": "PolicyGPT Enterprise backend is running.",
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
            "upload": f"{settings.api_prefix}/documents/upload",
        }

    return app


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        logger.warning(
            "application_exception",
            path=request.url.path,
            error_code=exc.error_code,
            status_code=exc.status_code,
            message=exc.message,
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
        logger.warning(
            "request_validation_error",
            path=request.url.path,
            errors=exc.errors(),
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": exc.errors(),
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
            path=request.url.path,
            error=str(exc),
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                },
            },
        )


app = create_app()