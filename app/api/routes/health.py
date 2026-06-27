from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/health", tags=["Health"])


def get_setting(name: str, default: Any = None) -> Any:
    """
    Safely read settings even if the config uses uppercase or lowercase field names.
    This prevents the health endpoint from crashing during local demo.
    """
    return getattr(settings, name, getattr(settings, name.lower(), default))


@router.get("")
def health_check() -> dict[str, Any]:
    """
    Lightweight backend health check.

    This endpoint does not call external LLM providers or run expensive checks.
    It confirms that the FastAPI app is running and exposes safe RAG config details.
    """
    return {
        "status": "healthy",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "app": {
            "name": get_setting("APP_NAME", "PolicyGPT Enterprise"),
            "version": get_setting("APP_VERSION", "0.1.0"),
            "environment": get_setting("APP_ENV", "development"),
            "debug": get_setting("DEBUG", False),
            "api_prefix": get_setting("API_PREFIX", "/api/v1"),
        },
        "rag": {
            "embedding_model": get_setting("EMBEDDING_MODEL_NAME"),
            "chunk_size_chars": get_setting("TEXT_CHUNK_SIZE_CHARS"),
            "chunk_overlap_chars": get_setting("TEXT_CHUNK_OVERLAP_CHARS"),
            "search_top_k_default": get_setting("SEARCH_TOP_K_DEFAULT"),
            "min_retrieval_score": get_setting("MIN_RETRIEVAL_SCORE"),
            "max_citation_cards": get_setting("MAX_CITATION_CARDS"),
        },
        "vector_store": {
            "provider": "ChromaDB",
            "collection_name": get_setting("CHROMA_COLLECTION_NAME"),
            "persist_directory": get_setting("CHROMA_PERSIST_DIRECTORY"),
        },
        "llm": {
            "enabled": get_setting("ENABLE_LLM_ANSWER"),
            "provider": get_setting("LLM_PROVIDER"),
            "groq_model": get_setting("GROQ_MODEL_NAME"),
            "openai_model": get_setting("OPENAI_MODEL_NAME"),
            "temperature": get_setting("LLM_TEMPERATURE"),
            "max_output_tokens": get_setting("LLM_MAX_OUTPUT_TOKENS"),
        },
    }