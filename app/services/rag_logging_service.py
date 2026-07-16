import re
from pathlib import Path
from threading import Lock

import structlog

from app.core.config import get_settings
from app.schemas.observability import RAGQueryLogEntry

logger = structlog.get_logger(__name__)

_RAG_LOG_WRITE_LOCK = Lock()
_MAX_ERROR_TYPE_LENGTH = 100
_MAX_ERROR_MESSAGE_LENGTH = 500
_SENSITIVE_ERROR_PATTERN = re.compile(
    r"api[_-]?key|groq_api_key|openai_api_key|evidence[_ -]?text|"
    r"system[_ -]?prompt|user[_ -]?prompt|provider[_ -]?payload|embedding",
    flags=re.IGNORECASE,
)


class RAGLoggingService:
    """Persist privacy-conscious, append-only RAG query metadata as JSONL."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def log_query(self, entry: RAGQueryLogEntry) -> None:
        if not self.settings.enable_rag_query_logging:
            return

        log_path = Path(self.settings.rag_query_log_path).expanduser()

        try:
            safe_entry = entry.model_copy(
                update={
                    "question": (
                        entry.question
                        if self.settings.rag_log_include_question
                        else None
                    ),
                    "error_type": self._sanitize_error_type(entry.error_type),
                    "error_message": self._sanitize_error_message(
                        entry.error_message
                    ),
                    "decision_reasons": self._sanitize_decision_reasons(
                        entry.decision_reasons
                    ),
                }
            )
            serialized_entry = safe_entry.model_dump_json()

            with _RAG_LOG_WRITE_LOCK:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with log_path.open("a", encoding="utf-8") as log_file:
                    log_file.write(serialized_entry + "\n")
        except Exception as exc:
            logger.warning(
                "rag_query_log_persistence_failed",
                log_path=str(log_path),
                error_type=type(exc).__name__,
            )

    def _sanitize_error_type(self, error_type: str | None) -> str | None:
        if error_type is None:
            return None

        sanitized = re.sub(r"[^A-Za-z0-9_.-]", "_", error_type.strip())
        return sanitized[:_MAX_ERROR_TYPE_LENGTH] or None

    def _sanitize_error_message(self, error_message: str | None) -> str | None:
        if error_message is None:
            return None

        sanitized = " ".join(error_message.split()).strip()

        if not sanitized:
            return None

        if _SENSITIVE_ERROR_PATTERN.search(sanitized):
            return "[redacted sensitive error message]"

        return sanitized[:_MAX_ERROR_MESSAGE_LENGTH]

    def _sanitize_decision_reasons(self, reasons: list[str]) -> list[str]:
        sanitized_reasons: list[str] = []

        for reason in reasons[:10]:
            sanitized = self._sanitize_error_message(reason)
            if sanitized:
                sanitized_reasons.append(sanitized)

        return sanitized_reasons
