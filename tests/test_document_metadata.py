import asyncio
import hashlib
import importlib.util
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile

from app.api.main import app
from app.api.routes.documents import document_service as api_document_service
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.models.document import Document, DocumentProcessingStage
from app.db.session import get_db_session
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import ExtractedPageText, PDFExtractionResult
from app.services.document_metadata_service import DocumentMetadataService
from app.services.document_service import DocumentService
from app.services.document_storage_service import DocumentStorageService
from app.services.text_cleaning_service import TextCleaningService


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as database_session:
        yield database_session
    engine.dispose()


def _document(*, sha256: str = "a" * 64, filename: str = "Policy.pdf") -> Document:
    identifier = "11111111-1111-4111-8111-111111111111"
    return Document(
        id=identifier,
        filename=filename,
        original_filename=filename,
        content_type="application/pdf",
        file_size_bytes=100,
        sha256=sha256,
        storage_key=f"documents/{identifier}/source.pdf",
    )


def test_database_configuration_is_required_outside_tests() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings(_env_file=None, APP_ENV="development", DATABASE_URL=None)


def test_database_configuration_is_safe_and_storage_is_configurable() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="development",
        DATABASE_URL="postgresql+psycopg://user:secret@localhost:5432/policygpt",
        DOCUMENT_STORAGE_DIR="tmp/policy-files",
    )
    assert settings.document_storage_dir == "tmp/policy-files"
    assert settings.safe_database_config["driver"] == "postgresql+psycopg"
    assert "host" not in settings.safe_database_config
    assert "secret" not in repr(settings.safe_database_config)


def test_document_defaults_create_uuid_timestamps_and_processing_state(session: Session) -> None:
    document = Document(
        filename="policy.pdf",
        original_filename="policy.pdf",
        content_type="application/pdf",
        file_size_bytes=4,
        sha256="b" * 64,
        storage_key="documents/22222222-2222-4222-8222-222222222222/source.pdf",
    )
    session.add(document)
    session.commit()
    assert len(document.id) == 36
    assert document.status == "processing"
    assert document.processing_stage == "received"
    assert document.created_at is not None
    assert document.updated_at is not None


def test_document_hash_is_unique(session: Session) -> None:
    first = _document()
    second = _document()
    second.id = "22222222-2222-4222-8222-222222222222"
    second.storage_key = f"documents/{second.id}/source.pdf"
    session.add(first)
    session.commit()
    session.add(second)
    with pytest.raises(IntegrityError):
        session.commit()


def test_ready_and_failed_states_require_consistent_metadata(session: Session) -> None:
    invalid_ready = _document(sha256="c" * 64)
    invalid_ready.status = "ready"
    invalid_ready.processing_stage = "complete"
    session.add(invalid_ready)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    invalid_failed = _document(sha256="d" * 64)
    invalid_failed.status = "failed"
    invalid_failed.processing_stage = "failed"
    session.add(invalid_failed)
    with pytest.raises(IntegrityError):
        session.commit()


def test_repository_create_lookup_filter_pagination_and_count(session: Session) -> None:
    repository = DocumentRepository(session)
    older = _document(sha256="1" * 64, filename="Benefits Policy.pdf")
    newer = _document(sha256="2" * 64, filename="Remote Policy.pdf")
    newer.id = "22222222-2222-4222-8222-222222222222"
    newer.storage_key = f"documents/{newer.id}/source.pdf"
    older.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    newer.created_at = datetime.now(timezone.utc)
    newer.status = "failed"
    newer.processing_stage = "failed"
    newer.error_code = "extraction_failed"
    repository.create(older)
    repository.create(newer)
    session.commit()

    assert repository.get_by_id(older.id) is older
    assert repository.get_by_sha256(newer.sha256) is newer
    assert repository.list_documents(limit=1, offset=0)[0] is newer
    assert repository.list_documents(limit=10, offset=0, status="failed") == [newer]
    assert repository.list_documents(limit=10, offset=0, filename="benefits") == [older]
    assert repository.count() == 2
    assert repository.count(status="failed") == 1


def test_repository_mark_ready_and_failed(session: Session) -> None:
    repository = DocumentRepository(session)
    ready = repository.create(_document(sha256="3" * 64))
    repository.mark_ready(
        ready,
        page_count=2,
        character_count=500,
        chunk_count=3,
        chroma_collection="policies",
        embedding_model="test-model",
        indexed_at=datetime.now(timezone.utc),
    )
    session.commit()
    assert (ready.status, ready.processing_stage, ready.chunk_count) == ("ready", "complete", 3)

    failed = _document(sha256="4" * 64)
    failed.id = "44444444-4444-4444-8444-444444444444"
    failed.storage_key = f"documents/{failed.id}/source.pdf"
    repository.create(failed)
    repository.mark_failed(failed, error_code="indexing_failed", error_message="Safe failure")
    session.commit()
    assert (failed.status, failed.processing_stage, failed.error_code) == (
        "failed",
        "failed",
        "indexing_failed",
    )


def test_storage_hash_size_atomic_move_and_safe_key(tmp_path: Path) -> None:
    storage = DocumentStorageService(tmp_path)
    content = b"%PDF-1.7\npolicy"
    upload = UploadFile(io.BytesIO(content), filename="../../unsafe.pdf")
    temporary = asyncio.run(storage.write_temporary(upload, max_size_bytes=1000))
    assert temporary.sha256 == hashlib.sha256(content).hexdigest()
    assert temporary.size_bytes == len(content)
    key = storage.build_storage_key("11111111-1111-4111-8111-111111111111")
    final_path = storage.finalize(temporary, key)
    assert final_path.read_bytes() == content
    assert "unsafe" not in str(final_path)
    assert not temporary.path.exists()


def test_storage_rejects_traversal_and_cleans_failed_temporary_file(tmp_path: Path) -> None:
    storage = DocumentStorageService(tmp_path)
    with pytest.raises(Exception, match="storage key"):
        storage.resolve_storage_key("../secret.pdf")
    upload = UploadFile(io.BytesIO(b"too large"), filename="policy.pdf")
    with pytest.raises(Exception, match="too large"):
        asyncio.run(storage.write_temporary(upload, max_size_bytes=2))
    assert list(tmp_path.glob(".upload-*.tmp")) == []


def test_duplicate_bytes_produce_the_same_hash(tmp_path: Path) -> None:
    storage = DocumentStorageService(tmp_path)
    first = asyncio.run(
        storage.write_temporary(UploadFile(io.BytesIO(b"same"), filename="a.pdf"), max_size_bytes=10)
    )
    second = asyncio.run(
        storage.write_temporary(UploadFile(io.BytesIO(b"same"), filename="b.pdf"), max_size_bytes=10)
    )
    assert first.sha256 == second.sha256
    storage.cleanup_temporary(first)
    storage.cleanup_temporary(second)


def test_metadata_service_lifecycle_and_safe_failure(session: Session) -> None:
    service = DocumentMetadataService(session)
    document = service.create(
        document_id="55555555-5555-4555-8555-555555555555",
        filename="policy.pdf",
        original_filename="policy.pdf",
        content_type="application/pdf",
        file_size_bytes=25,
        sha256="5" * 64,
        storage_key="documents/55555555-5555-4555-8555-555555555555/source.pdf",
    )
    service.update_stage(document, DocumentProcessingStage.STORED)
    service.mark_failed(
        document,
        error_code="extraction_failed",
        error_message=" Safe   message \n without a traceback ",
    )
    assert service.get_status(document.id).error_code == "extraction_failed"
    assert document.error_message == "Safe message without a traceback"


def _upload_service(tmp_path: Path) -> DocumentService:
    service = DocumentService.__new__(DocumentService)
    service.settings = get_settings()
    service.document_storage_service = DocumentStorageService(tmp_path)
    service.pdf_extraction_service = Mock()
    service.pdf_extraction_service.extract_text_from_pdf.return_value = PDFExtractionResult(
        page_count=1,
        total_characters=13,
        pages=[ExtractedPageText(page_number=1, text="Remote policy", char_count=13)],
    )
    service.text_cleaning_service = TextCleaningService()
    service.chunking_service = Mock()
    service.chunking_service.create_chunks.return_value = []
    service.embedding_service = Mock()
    service.embedding_service.embed_texts.return_value = []
    service.vector_store_service = Mock()
    service.vector_store_service.add_chunks.return_value = 0
    return service


def _upload(content: bytes = b"%PDF-1.7\npolicy") -> UploadFile:
    return UploadFile(io.BytesIO(content), filename="sample.pdf", headers={"content-type": "application/pdf"})


def test_upload_creates_ready_metadata_and_duplicate_skips_indexing(session: Session, tmp_path: Path) -> None:
    service = _upload_service(tmp_path)
    first = asyncio.run(service.process_pdf_upload(_upload(), session))
    second = asyncio.run(service.process_pdf_upload(_upload(), session))
    assert first.status == "ready"
    assert first.page_count == 1
    assert first.character_count == 13
    assert second.duplicate is True
    assert second.document_id == first.document_id
    assert service.vector_store_service.add_chunks.call_count == 1
    assert DocumentRepository(session).count() == 1


@pytest.mark.parametrize("status", ["processing", "ready", "failed"])
def test_all_existing_document_states_are_idempotent_duplicates(
    session: Session,
    tmp_path: Path,
    status: str,
) -> None:
    content = f"duplicate-{status}".encode()
    document = _document(sha256=hashlib.sha256(content).hexdigest())
    if status == "ready":
        document.status = "ready"
        document.processing_stage = "complete"
        document.page_count = 1
        document.character_count = 10
        document.chunk_count = 1
        document.indexed_at = datetime.now(timezone.utc)
    elif status == "failed":
        document.status = "failed"
        document.processing_stage = "failed"
        document.error_code = "extraction_failed"
        document.error_message = "Safe failure"
    session.add(document)
    session.commit()
    service = _upload_service(tmp_path)
    response = asyncio.run(service.process_pdf_upload(_upload(content), session))
    assert response.duplicate is True
    assert response.status == status
    service.vector_store_service.add_chunks.assert_not_called()


def test_database_failure_prevents_indexing_and_cleans_temporary_file(tmp_path: Path) -> None:
    class BrokenSession:
        def scalar(self, _statement):
            raise OperationalError("select", {}, RuntimeError("offline"))

        def rollback(self):
            pass

    service = _upload_service(tmp_path)
    with pytest.raises(Exception, match="metadata is temporarily unavailable"):
        asyncio.run(service.process_pdf_upload(_upload(b"db-offline"), BrokenSession()))
    service.vector_store_service.add_chunks.assert_not_called()
    assert list(tmp_path.glob(".upload-*.tmp")) == []


def test_document_table_contains_no_raw_content_or_embedding_columns() -> None:
    columns = set(Base.metadata.tables["documents"].columns.keys())
    assert columns.isdisjoint({"pdf_bytes", "raw_text", "chunk_text", "embedding_vector", "prompt"})


@pytest.mark.parametrize(
    ("failure_target", "error_code"),
    [("extract", "extraction_failed"), ("index", "indexing_failed")],
)
def test_upload_failure_is_persisted_safely(
    session: Session,
    tmp_path: Path,
    failure_target: str,
    error_code: str,
) -> None:
    service = _upload_service(tmp_path)
    if failure_target == "extract":
        service.pdf_extraction_service.extract_text_from_pdf.side_effect = RuntimeError("secret details")
    else:
        service.vector_store_service.add_chunks.side_effect = RuntimeError("secret details")
    with pytest.raises(Exception):
        asyncio.run(service.process_pdf_upload(_upload(failure_target.encode()), session))
    document = DocumentRepository(session).list_documents(limit=10, offset=0)[0]
    assert document.status == "failed"
    assert document.error_code == error_code
    assert "secret" not in (document.error_message or "")
    if failure_target == "index":
        service.vector_store_service.delete_document_chunks.assert_called_once_with(document.id)


def test_document_api_list_detail_status_and_filters(session: Session) -> None:
    metadata = DocumentMetadataService(session)
    document = metadata.create(
        document_id="66666666-6666-4666-8666-666666666666",
        filename="Remote Policy.pdf",
        original_filename="Remote Policy.pdf",
        content_type="application/pdf",
        file_size_bytes=20,
        sha256="6" * 64,
        storage_key="documents/66666666-6666-4666-8666-666666666666/source.pdf",
    )

    def override_session():
        yield session

    app.dependency_overrides[get_db_session] = override_session
    try:
        client = TestClient(app)
        listing = client.get("/api/v1/documents?limit=20&offset=0&status=processing&filename=remote")
        assert listing.status_code == 200
        assert listing.json()["total"] == 1
        detail = client.get(f"/api/v1/documents/{document.id}")
        assert detail.status_code == 200
        assert "storage_key" not in detail.json()
        status = client.get(f"/api/v1/documents/{document.id}/status")
        assert status.status_code == 200
        assert status.json()["processing_stage"] == "received"
        assert client.get("/api/v1/documents/77777777-7777-4777-8777-777777777777").status_code == 404
        assert client.get("/api/v1/documents/not-a-uuid").status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_document_api_database_outage_is_controlled() -> None:
    class BrokenSession:
        def scalars(self, _statement):
            raise OperationalError("select", {}, RuntimeError("offline"))

        def scalar(self, _statement):
            raise OperationalError("select", {}, RuntimeError("offline"))

        def rollback(self):
            pass

        def close(self):
            pass

    def override_session():
        yield BrokenSession()

    app.dependency_overrides[get_db_session] = override_session
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/documents")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert "postgresql" not in response.text.lower()

        original_add_chunks = api_document_service.vector_store_service.add_chunks
        api_document_service.vector_store_service.add_chunks = Mock()
        try:
            upload_response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("policy.pdf", b"%PDF-1.7\ntest", "application/pdf")},
            )
            assert upload_response.status_code == 503
            api_document_service.vector_store_service.add_chunks.assert_not_called()
        finally:
            api_document_service.vector_store_service.add_chunks = original_add_chunks
    finally:
        app.dependency_overrides.clear()


def test_migration_has_one_head_and_documents_metadata() -> None:
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["20260715_0001"]
    assert "documents" in Base.metadata.tables
    migration_path = Path("alembic/versions/20260715_0001_document_metadata.py")
    spec = importlib.util.spec_from_file_location("document_metadata_migration", migration_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "20260715_0001"
