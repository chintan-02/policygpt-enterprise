from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.config import Settings, get_settings
from app.db.session import get_engine
from app.schemas.health import (
    DependencyCheck,
    ProviderMode,
    ReadinessChecks,
    ReadinessResponse,
)
from app.services.vector_store_service import VectorStoreService


logger = structlog.get_logger(__name__)


class ReadinessService:
    """Perform provider-independent, read-only dependency checks."""

    def __init__(
        self,
        *,
        engine: Engine | None = None,
        vector_store: VectorStoreService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._engine = engine
        self._vector_store = vector_store
        self.settings = settings or get_settings()

    def check(self) -> ReadinessResponse:
        database = self._check_database()
        vector_store = self._check_vector_store()
        ready = database.status == "ready" and vector_store.status == "ready"
        return ReadinessResponse(
            status="ready" if ready else "not_ready",
            checks=ReadinessChecks(
                database=database,
                vector_store=vector_store,
            ),
            answer_generation=self._provider_mode(),
        )

    def _check_database(self) -> DependencyCheck:
        try:
            engine = self._engine or get_engine()
            with engine.connect() as connection:
                connection.execute(text("SELECT 1")).scalar_one()
            return DependencyCheck(status="ready")
        except Exception as exc:
            logger.error(
                "readiness_dependency_unavailable",
                dependency="database",
                error_type=type(exc).__name__,
            )
            return DependencyCheck(status="unavailable")

    def _check_vector_store(self) -> DependencyCheck:
        try:
            vector_store = self._vector_store or VectorStoreService(create_collection=False)
            vector_store.check_readiness()
            return DependencyCheck(status="ready")
        except Exception as exc:
            logger.error(
                "readiness_dependency_unavailable",
                dependency="vector_store",
                error_type=type(exc).__name__,
            )
            return DependencyCheck(status="unavailable")

    def _provider_mode(self) -> ProviderMode:
        provider = self.settings.llm_provider
        configured = (
            self.settings.enable_llm_answer
            and provider != "none"
            and (
                (provider == "groq" and bool(self.settings.groq_api_key))
                or (provider == "openai" and bool(self.settings.openai_api_key))
            )
        )
        return ProviderMode(
            status="configured" if configured else "citation_only_fallback",
            provider=provider,
        )
