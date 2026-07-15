from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

PageNumber = Annotated[int, Field(ge=1)]


class RAGQueryLogEntry(BaseModel):
    schema_version: int = Field(default=1, ge=1)
    query_id: str = Field(..., min_length=1)
    timestamp: datetime
    question: str | None
    question_length: int = Field(..., ge=0)
    answer_ready: bool
    evidence_status: str = Field(..., min_length=1)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    top_retrieval_score: float = Field(..., ge=0.0, le=1.0)
    average_retrieval_score: float = Field(..., ge=0.0, le=1.0)
    citation_count: int = Field(..., ge=0)
    retrieved_pages: list[PageNumber]
    retrieved_filenames: list[str]
    llm_provider: str = Field(..., min_length=1)
    model_name: str | None
    fallback_used: bool
    latency_ms: float = Field(..., ge=0.0)
    top_k: int = Field(..., ge=1)
    min_retrieval_score: float = Field(..., ge=0.0, le=1.0)
    error_type: str | None
    error_message: str | None

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp_to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")

        return value.astimezone(timezone.utc)
