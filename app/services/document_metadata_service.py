from datetime import datetime, timezone

import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import DatabaseUnavailableException, NotFoundException
from app.db.models.document import Document, DocumentProcessingStage
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentSummaryResponse,
)

logger = structlog.get_logger(__name__)


class DocumentMetadataService:
    """Own document lifecycle transactions and API-safe metadata mapping."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = DocumentRepository(session)

    def get_by_sha256(self, sha256: str) -> Document | None:
        return self._database_call(lambda: self.repository.get_by_sha256(sha256))

    def create(
        self,
        *,
        document_id: str,
        filename: str,
        original_filename: str,
        content_type: str,
        file_size_bytes: int,
        sha256: str,
        storage_key: str,
    ) -> Document:
        document = Document(
            id=document_id,
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            file_size_bytes=file_size_bytes,
            sha256=sha256,
            storage_key=storage_key,
        )

        def operation() -> Document:
            self.repository.create(document)
            self.session.commit()
            self.session.refresh(document)
            return document

        result = self._database_call(operation)
        logger.info(
            "document_metadata_created",
            document_id=result.id,
            filename=result.filename,
            sha256_prefix=result.sha256[:12],
            status=result.status,
            processing_stage=result.processing_stage,
        )
        return result

    def update_stage(self, document: Document, stage: DocumentProcessingStage) -> Document:
        def operation() -> Document:
            self.repository.update_processing_stage(document, stage.value)
            self.session.commit()
            self.session.refresh(document)
            return document

        result = self._database_call(operation)
        logger.info(
            "document_stage_updated",
            document_id=result.id,
            status=result.status,
            processing_stage=result.processing_stage,
        )
        return result

    def mark_ready(
        self,
        document: Document,
        *,
        page_count: int,
        character_count: int,
        chunk_count: int,
        chroma_collection: str,
        embedding_model: str,
    ) -> Document:
        indexed_at = datetime.now(timezone.utc)

        def operation() -> Document:
            self.repository.mark_ready(
                document,
                page_count=page_count,
                character_count=character_count,
                chunk_count=chunk_count,
                chroma_collection=chroma_collection,
                embedding_model=embedding_model,
                indexed_at=indexed_at,
            )
            self.session.commit()
            self.session.refresh(document)
            return document

        return self._database_call(operation)

    def mark_failed(self, document: Document, *, error_code: str, error_message: str) -> Document:
        safe_message = " ".join(error_message.split())[:500]

        def operation() -> Document:
            self.repository.mark_failed(
                document,
                error_code=error_code,
                error_message=safe_message,
            )
            self.session.commit()
            self.session.refresh(document)
            return document

        return self._database_call(operation)

    def list_documents(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None,
        filename: str | None,
    ) -> DocumentListResponse:
        def operation() -> tuple[list[Document], int]:
            return (
                self.repository.list_documents(
                    limit=limit,
                    offset=offset,
                    status=status,
                    filename=filename,
                ),
                self.repository.count(status=status, filename=filename),
            )

        documents, total = self._database_call(operation)
        return DocumentListResponse(
            items=[self.to_summary(document) for document in documents],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_detail(self, document_id: str) -> DocumentDetailResponse:
        document = self._database_call(lambda: self.repository.get_by_id(document_id))
        if document is None:
            raise NotFoundException("Document metadata was not found.")
        return self.to_detail(document)

    def get_status(self, document_id: str) -> DocumentStatusResponse:
        document = self._database_call(lambda: self.repository.get_by_id(document_id))
        if document is None:
            raise NotFoundException("Document metadata was not found.")
        return DocumentStatusResponse(
            document_id=document.id,
            status=document.status,
            processing_stage=document.processing_stage,
            page_count=document.page_count,
            chunk_count=document.chunk_count,
            error_code=document.error_code if document.status == "failed" else None,
            updated_at=document.updated_at,
        )

    @staticmethod
    def to_summary(document: Document) -> DocumentSummaryResponse:
        return DocumentSummaryResponse(
            document_id=document.id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.file_size_bytes,
            status=document.status,
            processing_stage=document.processing_stage,
            page_count=document.page_count,
            character_count=document.character_count,
            chunk_count=document.chunk_count,
            created_at=document.created_at,
            updated_at=document.updated_at,
            indexed_at=document.indexed_at,
        )

    @classmethod
    def to_detail(cls, document: Document) -> DocumentDetailResponse:
        summary = cls.to_summary(document)
        return DocumentDetailResponse(
            **summary.model_dump(),
            chroma_collection=document.chroma_collection,
            embedding_model=document.embedding_model,
            error_code=document.error_code if document.status == "failed" else None,
            error_message=document.error_message if document.status == "failed" else None,
        )

    def _database_call(self, operation):
        try:
            return operation()
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("database_operation_failed", error_type=type(exc).__name__)
            raise DatabaseUnavailableException() from exc
