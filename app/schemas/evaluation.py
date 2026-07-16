from datetime import datetime

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvaluationSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class EvaluationBackendHealth(EvaluationSchema):
    latency_ms: float | None = Field(default=None, ge=0.0)
    status: str | None = None


class EvaluationRunMetadata(EvaluationSchema):
    run_id: str = Field(..., min_length=1)
    started_at_utc: datetime | None = None
    completed_at_utc: datetime | None = None
    duration_ms: float | None = Field(default=None, ge=0.0)
    backend_base_label: str = "Configured backend"
    endpoint: str | None = None
    dataset_path: str | None = None
    dataset_sha256: str | None = None
    top_k: int | None = Field(default=None, ge=1)
    timeout_seconds: float | None = Field(default=None, ge=0.0)
    request_delay_seconds: float | None = Field(default=None, ge=0.0)
    question_count: int = Field(..., ge=0)
    backend_health: EvaluationBackendHealth | None = None
    duplicate_citation_warning: bool = False
    question_id: str | None = None
    limit: int | None = Field(default=None, ge=1)


class EvaluationSummary(EvaluationSchema):
    total_questions: int = Field(..., ge=0)
    supported_questions: int = Field(..., ge=0)
    unsupported_questions: int = Field(..., ge=0)
    passed_questions: int = Field(..., ge=0)
    failed_questions_count: int = Field(..., ge=0)
    request_error_count: int = Field(..., ge=0)
    answer_readiness_accuracy: float = Field(..., ge=0.0, le=1.0)
    fallback_accuracy: float = Field(..., ge=0.0, le=1.0)
    retrieval_page_hit_rate: float = Field(..., ge=0.0, le=1.0)
    keyword_match_rate: float = Field(..., ge=0.0, le=1.0)
    average_confidence: float = Field(..., ge=0.0, le=1.0)
    average_supported_confidence: float = Field(..., ge=0.0, le=1.0)
    average_latency_ms: float = Field(..., ge=0.0)
    average_citation_count: float = Field(..., ge=0.0)

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        if self.supported_questions + self.unsupported_questions != self.total_questions:
            raise ValueError("Evaluation support counts must equal total questions.")
        if self.passed_questions + self.failed_questions_count != self.total_questions:
            raise ValueError("Evaluation result counts must equal total questions.")
        if self.request_error_count > self.total_questions:
            raise ValueError("Evaluation request errors cannot exceed total questions.")
        return self


class EvaluationConfidenceBreakdown(EvaluationSchema):
    answerability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    top_retrieval_score: float | None = Field(default=None, ge=0.0, le=1.0)
    average_retrieval_score: float | None = Field(default=None, ge=0.0, le=1.0)
    retrieval_margin: float | None = Field(default=None, ge=0.0, le=1.0)
    lexical_coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    top_chunk_lexical_coverage: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    numeric_consistency: float | None = Field(default=None, ge=0.0, le=1.0)
    numeric_mismatch: bool = False
    scope_risk: bool = False
    direct_support: bool | None = None
    query_numeric_claims: list[str] = Field(default_factory=list)
    evidence_numeric_claims: list[str] = Field(default_factory=list)
    missing_numeric_claims: list[str] = Field(default_factory=list)
    matched_query_terms: list[str] = Field(default_factory=list)
    missing_query_terms: list[str] = Field(default_factory=list)
    decision_reasons: list[str] = Field(default_factory=list)
    scope_risk_reason: str | None = None


class EvaluationCase(EvaluationSchema):
    id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    difficulty: str = Field(..., min_length=1)
    evaluation_focus: list[str] = Field(default_factory=list)
    should_answer: bool
    answer_ready: bool
    readiness_correct: bool
    evidence_status: str = Field(..., min_length=1)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_breakdown: EvaluationConfidenceBreakdown | None = None
    answerability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    top_retrieval_score: float | None = Field(default=None, ge=0.0, le=1.0)
    average_retrieval_score: float | None = Field(default=None, ge=0.0, le=1.0)
    retrieval_margin: float | None = Field(default=None, ge=0.0, le=1.0)
    lexical_coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    top_chunk_lexical_coverage: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    numeric_consistency: float | None = Field(default=None, ge=0.0, le=1.0)
    numeric_mismatch: bool = False
    scope_risk: bool = False
    direct_support: bool | None = None
    decision_reasons: list[str] = Field(default_factory=list)
    expected_pages: list[int] = Field(default_factory=list)
    retrieved_pages: list[int] = Field(default_factory=list)
    page_hit: bool | None = None
    expected_answer_keywords: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    keyword_match_score: float | None = Field(default=None, ge=0.0, le=1.0)
    answer: str
    fallback_used: bool
    fallback_correct: bool | None = None
    citation_count: int = Field(..., ge=0)
    retrieved_filenames: list[str] = Field(default_factory=list)
    citation_scores: list[float] = Field(default_factory=list)
    top_citation_score: float | None = Field(default=None, ge=0.0)
    average_citation_score: float | None = Field(default=None, ge=0.0)
    duplicate_citation_count: int = Field(default=0, ge=0)
    latency_ms: float = Field(..., ge=0.0)
    llm_provider: str = Field(..., min_length=1)
    model_name: str | None = None
    case_passed: bool
    error_type: str | None = Field(default=None, max_length=120)
    provider_fallback_used: bool | None = None
    generation_attempt_count: int | None = Field(default=None, ge=1)
    generation_error_type: str | None = Field(default=None, max_length=120)


class EvaluationArtifactMetadata(EvaluationSchema):
    updated_at: datetime
    question_count: int = Field(..., ge=0)
    benchmark_question_count: int | None = Field(default=None, ge=0)
    is_partial: bool


class EvaluationArtifactResponse(EvaluationSchema):
    artifact: EvaluationArtifactMetadata
    run: EvaluationRunMetadata
    summary: EvaluationSummary
    results: list[EvaluationCase]
