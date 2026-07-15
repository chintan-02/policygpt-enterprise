from app.core.config import get_settings
from app.schemas.document import (
    CitationCard,
    DocumentEvidenceRequest,
    DocumentEvidenceResponse,
    DocumentSearchResult,
)
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService


class RetrievalService:
    """
    Convert raw semantic search results into citation-ready evidence.

    Design:
    - excerpt: short UI/API citation preview
    - evidence_text: longer internal evidence for LLM grounding
    - duplicate citations are skipped for cleaner answers
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()

    def retrieve_evidence(
        self,
        evidence_request: DocumentEvidenceRequest,
    ) -> DocumentEvidenceResponse:
        query_embedding = self.embedding_service.embed_query(evidence_request.query)

        raw_results = self.vector_store_service.search_similar_chunks(
            query_embedding=query_embedding,
            top_k=evidence_request.top_k,
        )

        raw_scores = [result.score for result in raw_results]
        top_retrieval_score = max(raw_scores, default=0.0)
        average_retrieval_score = (
            sum(raw_scores) / len(raw_scores) if raw_scores else 0.0
        )

        citation_cards = self._build_citation_cards(raw_results)

        evidence_status = self._get_evidence_status(citation_cards)
        confidence_score = self._calculate_confidence_score(citation_cards)
        answer_ready = evidence_status in {"strong", "moderate", "weak"}

        fallback_message = None

        if not answer_ready:
            fallback_message = (
                "I could not find enough supporting evidence in the uploaded "
                "documents to answer this question reliably."
            )

        return DocumentEvidenceResponse(
            query=evidence_request.query,
            top_k=evidence_request.top_k,
            answer_ready=answer_ready,
            evidence_status=evidence_status,
            confidence_score=confidence_score,
            top_retrieval_score=round(top_retrieval_score, 4),
            average_retrieval_score=round(average_retrieval_score, 4),
            min_retrieval_score=self.settings.min_retrieval_score,
            citation_count=len(citation_cards),
            citations=citation_cards,
            fallback_message=fallback_message,
        )

    def _build_citation_cards(
        self,
        raw_results: list[DocumentSearchResult],
    ) -> list[CitationCard]:
        citation_cards: list[CitationCard] = []
        seen_citation_keys: set[str] = set()

        for result in raw_results:
            if result.score < self.settings.min_retrieval_score:
                continue

            dedupe_key = self._build_dedupe_key(result)

            if dedupe_key in seen_citation_keys:
                continue

            seen_citation_keys.add(dedupe_key)

            excerpt = self._build_text_preview(
                text=result.text,
                max_chars=self.settings.citation_excerpt_max_chars,
            )

            evidence_text = self._build_text_preview(
                text=result.text,
                max_chars=self.settings.llm_evidence_max_chars,
            )

            citation_cards.append(
                CitationCard(
                    document_id=result.document_id,
                    filename=result.filename,
                    page_number=result.page_number,
                    section_title=result.section_title,
                    chunk_index=result.chunk_index,
                    excerpt=excerpt,
                    evidence_text=evidence_text,
                    retrieval_score=result.score,
                )
            )

            if len(citation_cards) >= self.settings.max_citation_cards:
                break

        return citation_cards

    def _build_dedupe_key(self, result: DocumentSearchResult) -> str:
        """
        Prevent duplicate citation cards when the same PDF is uploaded multiple times.

        We intentionally do not use document_id here because duplicate uploads
        create different document IDs for the same content.
        """

        normalized_text = " ".join(result.text.lower().split())
        text_fingerprint = normalized_text[:300]

        return "|".join(
            [
                result.filename.lower(),
                str(result.page_number),
                str(result.chunk_index),
                text_fingerprint,
            ]
        )

    def _build_text_preview(self, text: str, max_chars: int) -> str:
        text = " ".join(text.split()).strip()

        if len(text) <= max_chars:
            return text

        cutoff = text.rfind(" ", 0, max_chars)

        if cutoff == -1 or cutoff < max_chars // 2:
            cutoff = max_chars

        return text[:cutoff].strip() + "..."

    def _get_evidence_status(self, citation_cards: list[CitationCard]) -> str:
        if not citation_cards:
            return "insufficient"

        top_score = citation_cards[0].retrieval_score

        if top_score >= 0.65:
            return "strong"

        if top_score >= 0.45:
            return "moderate"

        if top_score >= self.settings.min_retrieval_score:
            return "weak"

        return "insufficient"

    def _calculate_confidence_score(
        self,
        citation_cards: list[CitationCard],
    ) -> float:
        if not citation_cards:
            return 0.0

        top_score = citation_cards[0].retrieval_score
        average_score = sum(card.retrieval_score for card in citation_cards) / len(
            citation_cards
        )

        confidence_score = (top_score * 0.7) + (average_score * 0.3)

        return round(max(0.0, min(1.0, confidence_score)), 4)
