from collections.abc import Generator
from functools import lru_cache

import structlog
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.exceptions import ConfigurationException

logger = structlog.get_logger(__name__)


def create_database_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    url = database_url or settings.database_url
    if not url:
        raise ConfigurationException("DATABASE_URL is required for document metadata.")

    options: dict[str, object] = {
        "pool_pre_ping": True,
        "echo": settings.database_echo,
    }
    if url.startswith("sqlite"):
        options.update(
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        options.update(
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout_seconds,
        )

    logger.info("database_engine_configured", **settings.safe_database_config)
    return create_engine(url, **options)


@lru_cache
def get_engine() -> Engine:
    return create_database_engine()


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
