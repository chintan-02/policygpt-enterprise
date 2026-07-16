from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine

from app.api.main import app
from app.api.routes.health import get_readiness_service
from app.core.config import Settings
from app.core.middleware import safe_request_id
from app.services.readiness_service import ReadinessService


class ReadyVectorStore:
    def check_readiness(self) -> None:
        return None


class UnavailableVectorStore:
    def check_readiness(self) -> None:
        raise RuntimeError("/secret/chroma/path should never be returned")


def test_liveness_is_lightweight_and_dependency_independent(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.readiness_service.get_engine",
        Mock(side_effect=RuntimeError("database offline")),
    )
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "operational"
    assert response.json()["service"] == "PolicyGPT Enterprise"
    assert response.json()["version"]
    assert response.json()["environment"] == "test"
    assert "vector_store" not in response.text
    assert "llm" not in response.text.lower()


def test_readiness_succeeds_without_provider_key() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="test",
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        LLM_PROVIDER="groq",
        GROQ_API_KEY=None,
    )
    service = ReadinessService(
        engine=create_engine("sqlite+pysqlite:///:memory:"),
        vector_store=ReadyVectorStore(),
        settings=settings,
    )
    app.dependency_overrides[get_readiness_service] = lambda: service
    try:
        response = TestClient(app).get("/api/v1/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"] == {
        "database": {"status": "ready"},
        "vector_store": {"status": "ready"},
    }
    assert response.json()["answer_generation"]["status"] == "citation_only_fallback"


def test_readiness_returns_503_for_database_without_internal_details() -> None:
    broken_engine = Mock()
    broken_engine.connect.side_effect = RuntimeError(
        "postgresql+psycopg://user:secret@internal-db:5432/policygpt"
    )
    service = ReadinessService(engine=broken_engine, vector_store=ReadyVectorStore())
    app.dependency_overrides[get_readiness_service] = lambda: service
    try:
        response = TestClient(app).get("/api/v1/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["checks"]["database"]["status"] == "unavailable"
    assert response.json()["checks"]["vector_store"]["status"] == "ready"
    assert "secret" not in response.text
    assert "internal-db" not in response.text


def test_readiness_returns_503_for_vector_store_without_internal_details() -> None:
    service = ReadinessService(
        engine=create_engine("sqlite+pysqlite:///:memory:"),
        vector_store=UnavailableVectorStore(),
    )
    app.dependency_overrides[get_readiness_service] = lambda: service
    try:
        response = TestClient(app).get("/api/v1/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["checks"]["database"]["status"] == "ready"
    assert response.json()["checks"]["vector_store"]["status"] == "unavailable"
    assert "/secret/chroma/path" not in response.text


def test_request_id_generation_preservation_and_replacement() -> None:
    client = TestClient(app)
    generated = client.get("/api/v1/health")
    preserved = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "portfolio-demo-123"},
    )
    unsafe = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "x" * 129},
    )

    assert generated.headers["X-Request-ID"]
    assert preserved.headers["X-Request-ID"] == "portfolio-demo-123"
    assert unsafe.headers["X-Request-ID"] != "x" * 129
    assert safe_request_id("bad\nvalue") != "bad\nvalue"
    assert safe_request_id("bad\rvalue") != "bad\rvalue"


def test_structured_error_contains_request_id() -> None:
    response = TestClient(app).get(
        "/api/v1/documents/not-a-uuid",
        headers={"X-Request-ID": "error-trace-123"},
    )
    assert response.status_code == 422
    assert response.headers["X-Request-ID"] == "error-trace-123"
    assert response.json()["error"]["request_id"] == "error-trace-123"


def test_api_security_headers_do_not_force_hsts() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.parametrize(
    "overrides",
    [
        {"TEXT_CHUNK_SIZE_CHARS": 100, "TEXT_CHUNK_OVERLAP_CHARS": 100},
        {
            "RAG_WEAK_CONFIDENCE_THRESHOLD": 0.7,
            "RAG_MODERATE_CONFIDENCE_THRESHOLD": 0.6,
        },
        {"LLM_PROVIDER": "invalid-provider"},
    ],
)
def test_invalid_production_configuration_fails_fast(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            APP_ENV="test",
            DATABASE_URL="sqlite+pysqlite:///:memory:",
            **overrides,
        )


def test_valid_citation_only_configuration_succeeds() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="test",
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        ENABLE_LLM_ANSWER=False,
        LLM_PROVIDER="none",
        GROQ_API_KEY=None,
        OPENAI_API_KEY=None,
    )
    assert settings.llm_provider == "none"
    assert settings.enable_llm_answer is False
