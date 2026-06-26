import logging
import sys
from typing import Any

import structlog

from app.core.config import get_settings


def configure_logging() -> None:
    """
    Configure structured logging for the backend.

    In development, logs are readable in the terminal.
    In production, JSON logs are easier to collect with logging tools.
    """

    settings = get_settings()

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.app_env == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.EventRenamer("message"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )