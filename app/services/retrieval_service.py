from app.core.config import get_settings
from app.schemas.document import (
    CitationCard,
    ConfidenceBreakdown,
    DocumentEvidenceRequest,
    DocumentEvidenceResponse,
    DocumentSearchResult,
)
from app.services.confidence_service import (
    ConfidenceAssessment,
    ConfidenceConfig,
    EvidenceCandidate,
    assess_confidence,
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
        self.confidence_config = ConfidenceConfig(
            candidate_retrieval_floor=self.settings.rag_candidate_retrieval_floor,
            direct_support_score_floor=(
                self.settings.rag_direct_support_score_floor
            ),
            direct_support_coverage_min=(
                self.settings.rag_direct_support_coverage_min
            ),
            weak_confidence_threshold=(
                self.settings.rag_weak_confidence_threshold
            ),
            moderate_confidence_threshold=(
                self.settings.rag_moderate_confidence_threshold
            ),
            strong_confidence_threshold=(
                self.settings.rag_strong_confidence_threshold
            ),
            max_evidence_chunks=(
                self.settings.rag_confidence_max_evidence_chunks
            ),
        )
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

        candidate_results = self._select_candidate_results(raw_results)
        assessment = assess_confidence(
            query=evidence_request.query,
            candidates=[
                EvidenceCandidate(text=result.text, score=result.score)
                for result in candidate_results
            ],
            config=self.confidence_config,
        )
        citation_cards = (
            self._build_citation_cards(candidate_results)
            if assessment.answer_ready
            else []
        )

        fallback_message = None

        if not assessment.answer_ready:
            fallback_message = (
                "I could not find enough supporting evidence in the uploaded "
                "documents to answer this question reliably."
            )

        return DocumentEvidenceResponse(
            query=evidence_request.query,
            top_k=evidence_request.top_k,
            answer_ready=assessment.answer_ready,
            evidence_status=assessment.evidence_status,
            confidence_score=assessment.public_confidence_score,
            top_retrieval_score=round(top_retrieval_score, 4),
            average_retrieval_score=round(average_retrieval_score, 4),
            min_retrieval_score=self.settings.rag_candidate_retrieval_floor,
            confidence_breakdown=self._build_confidence_breakdown(assessment),
            citation_count=len(citation_cards),
            citations=citation_cards,
            fallback_message=fallback_message,
        )

    def _select_candidate_results(
        self,
        raw_results: list[DocumentSearchResult],
    ) -> list[DocumentSearchResult]:
        candidate_results: list[DocumentSearchResult] = []
        seen_candidate_keys: set[str] = set()

        for result in sorted(raw_results, key=lambda item: item.score, reverse=True):
            if result.score < self.settings.rag_candidate_retrieval_floor:
                continue

            dedupe_key = self._build_dedupe_key(result)
            if dedupe_key in seen_candidate_keys:
                continue

            seen_candidate_keys.add(dedupe_key)
            candidate_results.append(result)

            if (
                len(candidate_results)
                >= self.settings.rag_confidence_max_evidence_chunks
            ):
                break

        return candidate_results

    def _build_citation_cards(
        self,
        raw_results: list[DocumentSearchResult],
    ) -> list[CitationCard]:
        citation_cards: list[CitationCard] = []
        seen_citation_keys: set[str] = set()

        for result in raw_results:
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

    def _build_confidence_breakdown(
        self,
        assessment: ConfidenceAssessment,
    ) -> ConfidenceBreakdown:
        return ConfidenceBreakdown(
            answerability_score=assessment.answerability_score,
            top_retrieval_score=assessment.top_retrieval_score,
            average_retrieval_score=assessment.average_retrieval_score,
            retrieval_margin=assessment.retrieval_margin,
            lexical_coverage=assessment.lexical_coverage,
            top_chunk_lexical_coverage=(
                assessment.top_chunk_lexical_coverage
            ),
            numeric_consistency=assessment.numeric_consistency,
            numeric_mismatch=assessment.numeric_mismatch,
            query_numeric_claims=assessment.query_numeric_claims,
            evidence_numeric_claims=assessment.evidence_numeric_claims,
            missing_numeric_claims=assessment.missing_numeric_claims,
            scope_risk=assessment.scope_risk,
            scope_risk_reason=assessment.scope_risk_reason,
            matched_query_terms=assessment.matched_query_terms,
            missing_query_terms=assessment.missing_query_terms,
            direct_support=assessment.direct_support,
            decision_reasons=assessment.decision_reasons,
        )
