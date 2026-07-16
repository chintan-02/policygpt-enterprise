from __future__ import annotations

import re
import time
from uuid import uuid4

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import get_settings


logger = structlog.get_logger(__name__)
REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    ),
    "Cache-Control": "no-store",
}


def safe_request_id(value: str | None) -> str:
    """Preserve a conservative caller ID or replace it with a UUID."""
    if value and REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


def request_id_from_scope(scope: Scope) -> str:
    state = scope.get("state", {})
    value = state.get("request_id") if isinstance(state, dict) else None
    return value if isinstance(value, str) else str(uuid4())


class RequestContextMiddleware:
    """Attach trace context, security headers, and one safe request log."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        settings = get_settings()
        self.environment = settings.app_env
        self.service_version = settings.app_version

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = safe_request_id(headers.get(REQUEST_ID_HEADER))
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.perf_counter()
        response_status = 500
        context = structlog.contextvars.bound_contextvars(request_id=request_id)

        async def send_with_headers(message: Message) -> None:
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = MutableHeaders(scope=message)
                response_headers[REQUEST_ID_HEADER] = request_id
                for name, value in SECURITY_HEADERS.items():
                    if name.lower() == "cache-control" and name in response_headers:
                        continue
                    response_headers[name] = value
            await send(message)

        with context:
            try:
                await self.app(scope, receive, send_with_headers)
            finally:
                route = scope.get("route")
                normalized_path = getattr(route, "path", None) or scope.get("path", "")
                latency_ms = round((time.perf_counter() - started) * 1000, 2)
                log_method = logger.debug if normalized_path.endswith(("/health", "/ready")) else logger.info
                log_method(
                    "http_request_completed",
                    method=scope.get("method"),
                    route=normalized_path,
                    status_code=response_status,
                    latency_ms=latency_ms,
                    environment=self.environment,
                    service_version=self.service_version,
                )
