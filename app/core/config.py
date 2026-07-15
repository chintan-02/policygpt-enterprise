import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="PolicyGPT Enterprise", alias="APP_NAME")

    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )

    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
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
        default=True,
        alias="RAG_LOG_INCLUDE_QUESTION",
    )

    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")

    cors_allowed_origins: str = Field(
        default="http://localhost:8501,http://localhost:3000,http://localhost:5173",
        alias="CORS_ALLOWED_ORIGINS",
    )

    max_pdf_upload_size_mb: int = Field(default=10, alias="MAX_PDF_UPLOAD_SIZE_MB")

    text_chunk_size_chars: int = Field(default=1200, alias="TEXT_CHUNK_SIZE_CHARS")
    text_chunk_overlap_chars: int = Field(default=200, alias="TEXT_CHUNK_OVERLAP_CHARS")

    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL_NAME",
    )
    embedding_batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")

    chroma_persist_directory: str = Field(
        default="data/chroma",
        alias="CHROMA_PERSIST_DIRECTORY",
    )
    chroma_collection_name: str = Field(
        default="policygpt_documents",
        alias="CHROMA_COLLECTION_NAME",
    )

    search_top_k_default: int = Field(default=5, alias="SEARCH_TOP_K_DEFAULT")

    min_retrieval_score: float = Field(default=0.45, alias="MIN_RETRIEVAL_SCORE")
    citation_excerpt_max_chars: int = Field(
        default=450,
        alias="CITATION_EXCERPT_MAX_CHARS",
    )
    llm_evidence_max_chars: int = Field(
        default=1200,
        alias="LLM_EVIDENCE_MAX_CHARS",
    )
    max_citation_cards: int = Field(default=5, alias="MAX_CITATION_CARDS")

    enable_llm_answer: bool = Field(default=True, alias="ENABLE_LLM_ANSWER")
    llm_provider: Literal["groq", "openai", "none"] = Field(
        default="groq",
        alias="LLM_PROVIDER",
    )
    llm_max_output_tokens: int = Field(default=700, alias="LLM_MAX_OUTPUT_TOKENS")
    llm_temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")

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
        "backend_host",
        "cors_allowed_origins",
        "embedding_model_name",
        "chroma_persist_directory",
        "chroma_collection_name",
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

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.cors_allowed_origins.strip()

        if not value:
            return []

        if value.startswith("["):
            parsed = json.loads(value)

            if not isinstance(parsed, list):
                raise ValueError("CORS_ALLOWED_ORIGINS must be a list.")

            return [str(origin).strip() for origin in parsed if str(origin).strip()]

        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @property
    def max_pdf_upload_size_bytes(self) -> int:
        return self.max_pdf_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
