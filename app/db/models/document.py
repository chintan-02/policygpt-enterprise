from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentProcessingStage(StrEnum):
    RECEIVED = "received"
    STORED = "stored"
    EXTRACTING = "extracting"
    CLEANING = "cleaning"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETE = "complete"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("file_size_bytes >= 0", name="ck_documents_file_size_nonnegative"),
        CheckConstraint("page_count IS NULL OR page_count >= 0", name="ck_documents_page_count_nonnegative"),
        CheckConstraint("character_count IS NULL OR character_count >= 0", name="ck_documents_character_count_nonnegative"),
        CheckConstraint("chunk_count IS NULL OR chunk_count >= 0", name="ck_documents_chunk_count_nonnegative"),
        CheckConstraint(
            "status IN ('processing', 'ready', 'failed')",
            name="ck_documents_status_value",
        ),
        CheckConstraint(
            "processing_stage IN ('received', 'stored', 'extracting', 'cleaning', 'chunking', 'embedding', 'indexing', 'complete', 'failed')",
            name="ck_documents_processing_stage_value",
        ),
        CheckConstraint(
            "status != 'ready' OR (processing_stage = 'complete' AND page_count IS NOT NULL AND character_count IS NOT NULL AND chunk_count IS NOT NULL AND indexed_at IS NOT NULL)",
            name="ck_documents_ready_metadata",
        ),
        CheckConstraint(
            "status != 'failed' OR (processing_stage = 'failed' AND error_code IS NOT NULL)",
            name="ck_documents_failed_metadata",
        ),
        Index("ix_documents_status", "status"),
        Index("ix_documents_created_at", "created_at"),
        Index("ix_documents_filename", "filename"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentStatus.PROCESSING.value,
    )
    processing_stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentProcessingStage.RECEIVED.value,
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    character_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chroma_collection: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
