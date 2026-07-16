from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.document import Document


class DocumentRepository:
    """SQLAlchemy persistence only; transactions are controlled by services."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, document: Document) -> Document:
        self.session.add(document)
        self.session.flush()
        return document

    def get_by_id(self, document_id: str) -> Document | None:
        return self.session.scalar(select(Document).where(Document.id == document_id))

    def get_by_sha256(self, sha256: str) -> Document | None:
        return self.session.scalar(select(Document).where(Document.sha256 == sha256))

    def list_documents(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        filename: str | None = None,
    ) -> list[Document]:
        statement = select(Document)
        if status:
            statement = statement.where(Document.status == status)
        if filename:
            statement = statement.where(Document.filename.ilike(f"%{filename}%"))
        statement = statement.order_by(Document.created_at.desc(), Document.id.desc())
        return list(self.session.scalars(statement.limit(limit).offset(offset)).all())

    def count(self, *, status: str | None = None, filename: str | None = None) -> int:
        statement = select(func.count()).select_from(Document)
        if status:
            statement = statement.where(Document.status == status)
        if filename:
            statement = statement.where(Document.filename.ilike(f"%{filename}%"))
        return int(self.session.scalar(statement) or 0)

    def update_processing_stage(self, document: Document, stage: str) -> Document:
        document.processing_stage = stage
        document.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return document

    def mark_ready(
        self,
        document: Document,
        *,
        page_count: int,
        character_count: int,
        chunk_count: int,
        chroma_collection: str,
        embedding_model: str,
        indexed_at: datetime,
    ) -> Document:
        document.status = "ready"
        document.processing_stage = "complete"
        document.page_count = page_count
        document.character_count = character_count
        document.chunk_count = chunk_count
        document.chroma_collection = chroma_collection
        document.embedding_model = embedding_model
        document.indexed_at = indexed_at
        document.error_code = None
        document.error_message = None
        document.updated_at = indexed_at
        self.session.flush()
        return document

    def mark_failed(self, document: Document, *, error_code: str, error_message: str) -> Document:
        document.status = "failed"
        document.processing_stage = "failed"
        document.error_code = error_code
        document.error_message = error_message[:500]
        document.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return document
