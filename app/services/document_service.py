import time
from datetime import datetime, timezone
from pathlib import PurePath
from uuid import uuid4

from fastapi import UploadFile
import structlog
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    AppException,
    BadRequestException,
    DatabaseUnavailableException,
    ServiceException,
)
from app.db.models.document import Document, DocumentProcessingStage
from app.schemas.document import (
    DocumentAnswerRequest,
    DocumentAnswerResponse,
    DocumentEvidenceRequest,
    DocumentEvidenceResponse,
    DocumentIngestionResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    ExtractedPageText,
)
from app.schemas.observability import RAGQueryLogEntry
from app.services.answer_generation_service import AnswerGenerationService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.document_metadata_service import DocumentMetadataService
from app.services.document_storage_service import (
    DocumentStorageService,
    TemporaryDocumentFile,
)
from app.services.pdf_extraction_service import PDFExtractionService
from app.services.rag_logging_service import RAGLoggingService
from app.services.retrieval_service import RetrievalService
from app.services.text_cleaning_service import TextCleaningService
from app.services.vector_store_service import VectorStoreService

logger = structlog.get_logger(__name__)


class DocumentService:
    """
    Service layer for document ingestion, retrieval, and citation-backed answers.
    """

    allowed_extensions = {".pdf"}
    allowed_content_types = {
        "application/pdf",
        "application/octet-stream",
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pdf_extraction_service = PDFExtractionService()
        self.text_cleaning_service = TextCleaningService()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()
        self.retrieval_service = RetrievalService()
        self.answer_generation_service = AnswerGenerationService()
        self.rag_logging_service = RAGLoggingService()
        self.document_storage_service = DocumentStorageService()

    async def process_pdf_upload(
        self,
        file: UploadFile,
        session: Session,
    ) -> DocumentIngestionResponse:
        settings = get_settings()

        original_filename = file.filename or ""

        if not original_filename.strip():
            raise BadRequestException("Uploaded file must have a filename.")

        file_extension = PurePath(original_filename).suffix.lower()

        if file_extension not in self.allowed_extensions:
            raise BadRequestException("Only PDF files are supported.")

        content_type = file.content_type or "unknown"

        if content_type not in self.allowed_content_types:
            raise BadRequestException(
                f"Invalid file content type: {content_type}. Only PDF files are supported."
            )

        filename = PurePath(original_filename).name
        metadata = DocumentMetadataService(session)
        temporary: TemporaryDocumentFile | None = None
        document: Document | None = None
        document_id: str | None = None
        failure_code = "storage_failed"
        indexing_started = False

        try:
            temporary = await self.document_storage_service.write_temporary(
                file,
                max_size_bytes=settings.max_pdf_upload_size_bytes,
            )

            duplicate = metadata.get_by_sha256(temporary.sha256)
            if duplicate is not None:
                self.document_storage_service.cleanup_temporary(temporary)
                logger.info(
                    "document_duplicate_detected",
                    document_id=duplicate.id,
                    filename=duplicate.filename,
                    sha256_prefix=duplicate.sha256[:12],
                    status=duplicate.status,
                    processing_stage=duplicate.processing_stage,
                )
                return self._build_duplicate_upload_response(duplicate)

            document_id = str(uuid4())
            storage_key = self.document_storage_service.build_storage_key(document_id)
            failure_code = "metadata_update_failed"
            document = metadata.create(
                document_id=document_id,
                filename=filename,
                original_filename=original_filename,
                content_type=content_type,
                file_size_bytes=temporary.size_bytes,
                sha256=temporary.sha256,
                storage_key=storage_key,
            )

            failure_code = "storage_failed"
            self.document_storage_service.finalize(temporary, storage_key)
            temporary = None
            metadata.update_stage(document, DocumentProcessingStage.STORED)
            logger.info(
                "document_storage_completed",
                document_id=document.id,
                filename=document.filename,
                sha256_prefix=document.sha256[:12],
            )

            failure_code = "extraction_failed"
            metadata.update_stage(document, DocumentProcessingStage.EXTRACTING)
            pdf_bytes = self.document_storage_service.read_bytes(storage_key)
            extraction_result = self.pdf_extraction_service.extract_text_from_pdf(pdf_bytes)

            failure_code = "cleaning_failed"
            metadata.update_stage(document, DocumentProcessingStage.CLEANING)
            cleaned_pages, page_section_titles = self._clean_extracted_pages(
                pages=extraction_result.pages,
            )
            total_characters = sum(page.char_count for page in cleaned_pages)
            is_text_extractable = total_characters > 0

            failure_code = "chunking_failed"
            metadata.update_stage(document, DocumentProcessingStage.CHUNKING)
            chunks = self.chunking_service.create_chunks(
                document_id=document.id,
                filename=filename,
                pages=cleaned_pages,
                page_section_titles=page_section_titles,
                chunk_size_chars=settings.text_chunk_size_chars,
                chunk_overlap_chars=settings.text_chunk_overlap_chars,
            )

            failure_code = "embedding_failed"
            metadata.update_stage(document, DocumentProcessingStage.EMBEDDING)
            embeddings = self.embedding_service.embed_texts([chunk.text for chunk in chunks])

            failure_code = "indexing_failed"
            metadata.update_stage(document, DocumentProcessingStage.INDEXING)
            indexing_started = True
            stored_chunk_count = self.vector_store_service.add_chunks(
                chunks=chunks,
                embeddings=embeddings,
            )
            if stored_chunk_count != len(chunks):
                raise ServiceException("Document indexing did not store every chunk.")

            failure_code = "metadata_update_failed"
            if not self.document_storage_service.exists(storage_key):
                raise ServiceException("Stored document source is unavailable.")
            document = metadata.mark_ready(
                document,
                page_count=extraction_result.page_count,
                character_count=total_characters,
                chunk_count=stored_chunk_count,
                chroma_collection=settings.chroma_collection_name,
                embedding_model=settings.embedding_model_name,
            )

            logger.info(
                "document_indexing_completed",
                document_id=document.id,
                filename=document.filename,
                status=document.status,
                processing_stage=document.processing_stage,
                page_count=document.page_count,
                chunk_count=document.chunk_count,
            )

            preview_text = self._build_preview_text(
                pages_text=[page.text for page in cleaned_pages],
                max_characters=1000,
            )
            message = (
                "PDF uploaded, text extracted, chunks embedded, and stored in ChromaDB successfully."
                if is_text_extractable and stored_chunk_count > 0
                else "PDF uploaded successfully, but no selectable text was found."
            )
            return DocumentIngestionResponse(
                document_id=document.id,
                filename=document.filename,
                content_type=document.content_type,
                size_bytes=document.file_size_bytes,
                page_count=document.page_count or 0,
                total_characters=document.character_count or 0,
                is_text_extractable=is_text_extractable,
                chunk_count=document.chunk_count or 0,
                stored_chunk_count=document.chunk_count or 0,
                collection_name=settings.chroma_collection_name,
                preview_text=preview_text,
                sample_chunks=chunks[:3],
                message=message,
                status=document.status,
                processing_stage=document.processing_stage,
                character_count=document.character_count,
                duplicate=False,
                created_at=document.created_at,
                indexed_at=document.indexed_at,
            )
        except Exception as exc:
            self.document_storage_service.cleanup_temporary(temporary)
            if indexing_started and document is not None:
                try:
                    self.vector_store_service.delete_document_chunks(document.id)
                except Exception:
                    logger.exception(
                        "document_vector_cleanup_failed",
                        document_id=document_id,
                    )
            if document is not None:
                try:
                    metadata.mark_failed(
                        document,
                        error_code=failure_code,
                        error_message=self._safe_ingestion_error_message(failure_code),
                    )
                except DatabaseUnavailableException:
                    logger.exception(
                        "document_failure_metadata_unavailable",
                        document_id=document_id,
                        error_code=failure_code,
                    )
            logger.exception(
                "document_ingestion_failed",
                document_id=document_id,
                filename=filename,
                error_code=failure_code,
            )
            if isinstance(exc, AppException):
                raise
            raise ServiceException(self._safe_ingestion_error_message(failure_code)) from exc

    def search_documents(
        self,
        search_request: DocumentSearchRequest,
    ) -> DocumentSearchResponse:
        query_embedding = self.embedding_service.embed_query(search_request.query)

        results = self.vector_store_service.search_similar_chunks(
            query_embedding=query_embedding,
            top_k=search_request.top_k,
        )

        return DocumentSearchResponse(
            query=search_request.query,
            top_k=search_request.top_k,
            result_count=len(results),
            results=results,
        )

    def retrieve_evidence(
        self,
        evidence_request: DocumentEvidenceRequest,
    ) -> DocumentEvidenceResponse:
        return self.retrieval_service.retrieve_evidence(evidence_request)

    def answer_question(
        self,
        answer_request: DocumentAnswerRequest,
    ) -> DocumentAnswerResponse:
        query_id = str(uuid4())
        started_at = time.perf_counter()
        evidence_response: DocumentEvidenceResponse | None = None
        response: DocumentAnswerResponse | None = None
        llm_provider = "none"
        model_name: str | None = None
        fallback_used = True

        try:
            evidence_response = self.retrieve_evidence(
                DocumentEvidenceRequest(
                    query=answer_request.question,
                    top_k=answer_request.top_k,
                )
            )

            if not evidence_response.answer_ready:
                fallback_answer = evidence_response.fallback_message or (
                    "I could not find enough supporting evidence in the uploaded "
                    "documents to answer this reliably."
                )

                response = DocumentAnswerResponse(
                    question=answer_request.question,
                    answer=fallback_answer,
                    answer_ready=False,
                    evidence_status=evidence_response.evidence_status,
                    confidence_score=evidence_response.confidence_score,
                    confidence_breakdown=evidence_response.confidence_breakdown,
                    citation_count=evidence_response.citation_count,
                    citations=evidence_response.citations,
                    llm_provider=llm_provider,
                    model_name=model_name,
                    fallback_used=fallback_used,
                )
            else:
                if self.settings.enable_llm_answer:
                    llm_provider = self.settings.llm_provider

                    if llm_provider == "groq":
                        model_name = self.settings.groq_model_name
                    elif llm_provider == "openai":
                        model_name = self.settings.openai_model_name

                answer, model_name, llm_provider, fallback_used = (
                    self.answer_generation_service.generate_answer(
                        question=answer_request.question,
                        citations=evidence_response.citations,
                    )
                )

                response = DocumentAnswerResponse(
                    question=answer_request.question,
                    answer=answer,
                    answer_ready=True,
                    evidence_status=evidence_response.evidence_status,
                    confidence_score=evidence_response.confidence_score,
                    confidence_breakdown=evidence_response.confidence_breakdown,
                    citation_count=evidence_response.citation_count,
                    citations=evidence_response.citations,
                    llm_provider=llm_provider,
                    model_name=model_name,
                    fallback_used=fallback_used,
                )

            self._log_rag_query(
                query_id=query_id,
                started_at=started_at,
                answer_request=answer_request,
                evidence_response=evidence_response,
                response=response,
                llm_provider=llm_provider,
                model_name=model_name,
                fallback_used=fallback_used,
            )
            return response
        except Exception as exc:
            self._log_rag_query(
                query_id=query_id,
                started_at=started_at,
                answer_request=answer_request,
                evidence_response=evidence_response,
                response=None,
                llm_provider=llm_provider,
                model_name=model_name,
                fallback_used=True,
                error=exc,
            )
            raise

    def _log_rag_query(
        self,
        *,
        query_id: str,
        started_at: float,
        answer_request: DocumentAnswerRequest,
        evidence_response: DocumentEvidenceResponse | None,
        response: DocumentAnswerResponse | None,
        llm_provider: str,
        model_name: str | None,
        fallback_used: bool,
        error: Exception | None = None,
    ) -> None:
        try:
            citations = evidence_response.citations if evidence_response else []
            confidence_breakdown = (
                evidence_response.confidence_breakdown
                if evidence_response
                else None
            )
            retrieved_pages = sorted({citation.page_number for citation in citations})
            retrieved_filenames = sorted(
                {citation.filename for citation in citations if citation.filename}
            )
            latency_ms = round(
                max(0.0, (time.perf_counter() - started_at) * 1000),
                2,
            )

            entry = RAGQueryLogEntry(
                query_id=query_id,
                timestamp=datetime.now(timezone.utc),
                question=(
                    answer_request.question
                    if self.settings.rag_log_include_question
                    else None
                ),
                question_length=len(answer_request.question),
                answer_ready=response.answer_ready if response else False,
                evidence_status=(
                    evidence_response.evidence_status
                    if evidence_response
                    else "error"
                ),
                confidence_score=(
                    evidence_response.confidence_score if evidence_response else 0.0
                ),
                answerability_score=(
                    confidence_breakdown.answerability_score
                    if confidence_breakdown
                    else 0.0
                ),
                top_retrieval_score=(
                    confidence_breakdown.top_retrieval_score
                    if confidence_breakdown
                    else evidence_response.top_retrieval_score
                    if evidence_response
                    else 0.0
                ),
                average_retrieval_score=(
                    confidence_breakdown.average_retrieval_score
                    if confidence_breakdown
                    else evidence_response.average_retrieval_score
                    if evidence_response
                    else 0.0
                ),
                retrieval_margin=(
                    confidence_breakdown.retrieval_margin
                    if confidence_breakdown
                    else 0.0
                ),
                lexical_coverage=(
                    confidence_breakdown.lexical_coverage
                    if confidence_breakdown
                    else 0.0
                ),
                top_chunk_lexical_coverage=(
                    confidence_breakdown.top_chunk_lexical_coverage
                    if confidence_breakdown
                    else 0.0
                ),
                numeric_mismatch=(
                    confidence_breakdown.numeric_mismatch
                    if confidence_breakdown
                    else False
                ),
                scope_risk=(
                    confidence_breakdown.scope_risk
                    if confidence_breakdown
                    else False
                ),
                direct_support=(
                    confidence_breakdown.direct_support
                    if confidence_breakdown
                    else False
                ),
                decision_reasons=(
                    confidence_breakdown.decision_reasons
                    if confidence_breakdown
                    else []
                ),
                citation_count=(
                    evidence_response.citation_count if evidence_response else 0
                ),
                retrieved_pages=retrieved_pages,
                retrieved_filenames=retrieved_filenames,
                llm_provider=llm_provider,
                model_name=model_name,
                fallback_used=fallback_used,
                latency_ms=latency_ms,
                top_k=answer_request.top_k,
                min_retrieval_score=(
                    evidence_response.min_retrieval_score
                    if evidence_response
                    else self.settings.min_retrieval_score
                ),
                error_type=type(error).__name__ if error else None,
                error_message=str(error) if error else None,
            )
            self.rag_logging_service.log_query(entry)
        except Exception as exc:
            logger.warning(
                "rag_query_log_entry_failed",
                query_id=query_id,
                error_type=type(exc).__name__,
            )

    def _clean_extracted_pages(
        self,
        pages: list[ExtractedPageText],
    ) -> tuple[list[ExtractedPageText], dict[int, str | None]]:
        cleaned_pages: list[ExtractedPageText] = []
        page_section_titles: dict[int, str | None] = {}

        for page in pages:
            cleaned_text = self.text_cleaning_service.clean_page_text(page.text)

            page_section_titles[page.page_number] = (
                self.text_cleaning_service.infer_section_title(
                    original_text=page.text,
                    fallback=f"Page {page.page_number}",
                )
            )

            cleaned_pages.append(
                ExtractedPageText(
                    page_number=page.page_number,
                    text=cleaned_text,
                    char_count=len(cleaned_text),
                )
            )

        return cleaned_pages, page_section_titles

    def _build_preview_text(
        self,
        pages_text: list[str],
        max_characters: int = 1000,
    ) -> str:
        combined_text = " ".join(text for text in pages_text if text).strip()

        if len(combined_text) <= max_characters:
            return combined_text

        return combined_text[:max_characters].strip() + "..."

    def _build_duplicate_upload_response(self, document: Document) -> DocumentIngestionResponse:
        page_count = document.page_count or 0
        character_count = document.character_count or 0
        chunk_count = document.chunk_count or 0
        return DocumentIngestionResponse(
            document_id=document.id,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.file_size_bytes,
            page_count=page_count,
            total_characters=character_count,
            is_text_extractable=character_count > 0,
            chunk_count=chunk_count,
            stored_chunk_count=chunk_count,
            collection_name=document.chroma_collection or self.settings.chroma_collection_name,
            preview_text="",
            sample_chunks=[],
            message="This PDF already exists; the existing document metadata was returned.",
            status=document.status,
            processing_stage=document.processing_stage,
            character_count=document.character_count,
            duplicate=True,
            created_at=document.created_at,
            indexed_at=document.indexed_at,
        )

    @staticmethod
    def _safe_ingestion_error_message(error_code: str) -> str:
        messages = {
            "storage_failed": "The PDF source could not be stored safely.",
            "extraction_failed": "Text could not be extracted from the PDF.",
            "cleaning_failed": "Extracted PDF text could not be prepared.",
            "chunking_failed": "The PDF could not be divided into indexable sections.",
            "embedding_failed": "Document sections could not be embedded.",
            "indexing_failed": "Document sections could not be indexed.",
            "metadata_update_failed": "Document metadata could not be updated.",
        }
        return messages.get(error_code, "Document ingestion could not be completed.")
