from pathlib import PurePath
import json
from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="PolicyGPT Enterprise", alias="APP_NAME")

    app_env: Literal["development", "staging", "production", "test"] = Field(
        default="development",
        alias="APP_ENV",
    )

    app_version: str = Field(default="0.3.0", alias="APP_VERSION")
    debug: bool = Field(default=True, alias="DEBUG")

    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    enable_rag_query_logging: bool = Field(
        default=True,
        alias="ENABLE_RAG_QUERY_LOGGING",
    )
    rag_query_log_path: str = Field(
        default="logs/rag_queries.jsonl",
        alias="RAG_QUERY_LOG_PATH",
    )
    rag_log_include_question: bool = Field(
        default=False,
        alias="RAG_LOG_INCLUDE_QUESTION",
    )
    evaluation_results_path: str = Field(
        default="eval/results/latest_eval_results.json",
        alias="POLICYGPT_EVAL_RESULTS_PATH",
    )

    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, gt=0, le=65535, alias="BACKEND_PORT")

    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ALLOWED_ORIGINS",
    )

    max_pdf_upload_size_mb: int = Field(default=10, gt=0, alias="MAX_PDF_UPLOAD_SIZE_MB")

    text_chunk_size_chars: int = Field(default=1200, gt=0, alias="TEXT_CHUNK_SIZE_CHARS")
    text_chunk_overlap_chars: int = Field(default=200, ge=0, alias="TEXT_CHUNK_OVERLAP_CHARS")

    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL_NAME",
    )
    embedding_batch_size: int = Field(default=32, gt=0, alias="EMBEDDING_BATCH_SIZE")

    chroma_persist_directory: str = Field(
        default="data/chroma",
        alias="CHROMA_PERSIST_DIRECTORY",
    )
    chroma_collection_name: str = Field(
        default="policygpt_documents",
        alias="CHROMA_COLLECTION_NAME",
    )

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    database_pool_size: int = Field(default=5, ge=1, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(
        default=5,
        ge=0,
        alias="DATABASE_MAX_OVERFLOW",
    )
    database_pool_timeout_seconds: int = Field(
        default=30,
        ge=1,
        alias="DATABASE_POOL_TIMEOUT_SECONDS",
    )
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")
    document_storage_dir: str = Field(
        default="data/uploads",
        alias="DOCUMENT_STORAGE_DIR",
    )

    search_top_k_default: int = Field(default=5, gt=0, alias="SEARCH_TOP_K_DEFAULT")

    min_retrieval_score: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
        alias="MIN_RETRIEVAL_SCORE",
    )
    rag_candidate_retrieval_floor: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        alias="RAG_CANDIDATE_RETRIEVAL_FLOOR",
    )
    rag_direct_support_score_floor: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        alias="RAG_DIRECT_SUPPORT_SCORE_FLOOR",
    )
    rag_direct_support_coverage_min: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        alias="RAG_DIRECT_SUPPORT_COVERAGE_MIN",
    )
    rag_weak_confidence_threshold: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        alias="RAG_WEAK_CONFIDENCE_THRESHOLD",
    )
    rag_moderate_confidence_threshold: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        alias="RAG_MODERATE_CONFIDENCE_THRESHOLD",
    )
    rag_strong_confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        alias="RAG_STRONG_CONFIDENCE_THRESHOLD",
    )
    rag_confidence_max_evidence_chunks: int = Field(
        default=3,
        ge=1,
        alias="RAG_CONFIDENCE_MAX_EVIDENCE_CHUNKS",
    )
    citation_excerpt_max_chars: int = Field(
        default=450,
        gt=0,
        alias="CITATION_EXCERPT_MAX_CHARS",
    )
    llm_evidence_max_chars: int = Field(
        default=1200,
        gt=0,
        alias="LLM_EVIDENCE_MAX_CHARS",
    )
    max_citation_cards: int = Field(default=5, gt=0, alias="MAX_CITATION_CARDS")

    enable_llm_answer: bool = Field(default=True, alias="ENABLE_LLM_ANSWER")
    llm_provider: Literal["groq", "openai", "none"] = Field(
        default="groq",
        alias="LLM_PROVIDER",
    )
    llm_max_output_tokens: int = Field(default=700, gt=0, alias="LLM_MAX_OUTPUT_TOKENS")
    llm_temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")
    llm_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        alias="LLM_MAX_RETRIES",
    )
    llm_retry_base_delay_seconds: float = Field(
        default=1.0,
        ge=0.0,
        alias="LLM_RETRY_BASE_DELAY_SECONDS",
    )
    llm_retry_max_delay_seconds: float = Field(
        default=5.0,
        ge=0.0,
        alias="LLM_RETRY_MAX_DELAY_SECONDS",
    )

    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        alias="GROQ_BASE_URL",
    )
    groq_model_name: str = Field(
        default="llama-3.3-70b-versatile",
        alias="GROQ_MODEL_NAME",
    )

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model_name: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_NAME")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "app_name",
        "app_env",
        "app_version",
        "api_prefix",
        "log_level",
        "rag_query_log_path",
        "evaluation_results_path",
        "backend_host",
        "cors_allowed_origins",
        "embedding_model_name",
        "chroma_persist_directory",
        "chroma_collection_name",
        "database_url",
        "document_storage_dir",
        "llm_provider",
        "groq_api_key",
        "groq_base_url",
        "groq_model_name",
        "openai_api_key",
        "openai_model_name",
        mode="before",
    )
    @classmethod
    def strip_wrapping_quotes(cls, value: str | None) -> str | None:
        if value is None:
            return value

        if not isinstance(value, str):
            return value

        value = value.strip()

        if not value:
            return None

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1].strip()

        return value

    @model_validator(mode="after")
    def validate_ordered_settings(self) -> Self:
        if self.app_env != "test" and not self.database_url:
            raise ValueError("DATABASE_URL is required outside tests.")

        if (
            self.rag_candidate_retrieval_floor
            > self.rag_direct_support_score_floor
        ):
            raise ValueError(
                "RAG_CANDIDATE_RETRIEVAL_FLOOR must be less than or equal to "
                "RAG_DIRECT_SUPPORT_SCORE_FLOOR."
            )

        if not (
            self.rag_weak_confidence_threshold
            < self.rag_moderate_confidence_threshold
            < self.rag_strong_confidence_threshold
        ):
            raise ValueError(
                "RAG confidence thresholds must satisfy weak < moderate < strong."
            )

        if (
            self.llm_retry_max_delay_seconds
            < self.llm_retry_base_delay_seconds
        ):
            raise ValueError(
                "LLM_RETRY_MAX_DELAY_SECONDS must be greater than or equal to "
                "LLM_RETRY_BASE_DELAY_SECONDS."
            )

        if not self.api_prefix.startswith("/") or self.api_prefix.endswith("/"):
            raise ValueError("API_PREFIX must start with '/' and must not end with '/'.")

        if self.text_chunk_overlap_chars >= self.text_chunk_size_chars:
            raise ValueError(
                "TEXT_CHUNK_OVERLAP_CHARS must be smaller than TEXT_CHUNK_SIZE_CHARS."
            )

        self._validate_non_empty_path(self.rag_query_log_path, "RAG_QUERY_LOG_PATH")
        self._validate_non_empty_path(
            self.evaluation_results_path,
            "POLICYGPT_EVAL_RESULTS_PATH",
        )
        self._validate_non_empty_path(
            self.chroma_persist_directory,
            "CHROMA_PERSIST_DIRECTORY",
        )
        self._validate_non_empty_path(self.document_storage_dir, "DOCUMENT_STORAGE_DIR")

        if not self.chroma_collection_name:
            raise ValueError("CHROMA_COLLECTION_NAME must not be empty.")

        if self.database_url:
            database_scheme = urlsplit(self.database_url).scheme
            allowed_schemes = {"postgresql", "postgresql+psycopg"}
            if self.app_env == "test":
                allowed_schemes.update({"sqlite", "sqlite+pysqlite"})
            if database_scheme not in allowed_schemes:
                raise ValueError("DATABASE_URL must use PostgreSQL with psycopg.")

        # Parse and validate before the CORS middleware is created.
        self._validated_cors_origins()

        return self

    @staticmethod
    def _validate_non_empty_path(value: str, setting_name: str) -> None:
        if not value or any(character in value for character in ("\x00", "\r", "\n")):
            raise ValueError(f"{setting_name} must be a non-empty safe path.")
        if str(PurePath(value)) in {"", "."}:
            raise ValueError(f"{setting_name} must identify a file or directory.")

    @property
    def safe_database_config(self) -> dict[str, str | int | bool | None]:
        """Return connection diagnostics without credentials or the full URL."""
        parsed = urlsplit(self.database_url or "")
        return {
            "driver": parsed.scheme or None,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "pool_timeout_seconds": self.database_pool_timeout_seconds,
            "echo": self.database_echo,
        }

    @property
    def cors_origins_list(self) -> list[str]:
        return self._validated_cors_origins()

    def _validated_cors_origins(self) -> list[str]:
        value = self.cors_allowed_origins.strip()

        if not value:
            return []

        if value.startswith("["):
            parsed = json.loads(value)

            if not isinstance(parsed, list):
                raise ValueError("CORS_ALLOWED_ORIGINS must be a list.")

            origins = [str(origin).strip() for origin in parsed if str(origin).strip()]
        else:
            origins = [origin.strip() for origin in value.split(",") if origin.strip()]

        normalized: list[str] = []
        for origin in origins:
            if origin == "*":
                raise ValueError("CORS_ALLOWED_ORIGINS cannot contain '*'.")
            parsed_origin = urlsplit(origin)
            if (
                parsed_origin.scheme not in {"http", "https"}
                or not parsed_origin.netloc
                or parsed_origin.username
                or parsed_origin.password
                or parsed_origin.path not in {"", "/"}
                or parsed_origin.query
                or parsed_origin.fragment
            ):
                raise ValueError("CORS_ALLOWED_ORIGINS contains a malformed origin.")
            clean_origin = f"{parsed_origin.scheme.lower()}://{parsed_origin.netloc.lower()}"
            if clean_origin not in normalized:
                normalized.append(clean_origin)
        return normalized

    @property
    def max_pdf_upload_size_bytes(self) -> int:
        return self.max_pdf_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
