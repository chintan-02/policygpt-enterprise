from pydantic import BaseModel, Field


class ExtractedPageText(BaseModel):
    page_number: int = Field(..., ge=1)
    text: str
    char_count: int = Field(..., ge=0)


class PDFExtractionResult(BaseModel):
    page_count: int = Field(..., ge=0)
    total_characters: int = Field(..., ge=0)
    pages: list[ExtractedPageText]


class DocumentChunk(BaseModel):
    document_id: str
    filename: str
    page_number: int = Field(..., ge=1)
    chunk_index: int = Field(..., ge=0)
    section_title: str | None = None
    text: str
    char_count: int = Field(..., ge=0)


class DocumentIngestionResponse(BaseModel):
    success: bool = Field(default=True)
    document_id: str
    filename: str
    content_type: str
    size_bytes: int = Field(..., ge=0)

    page_count: int = Field(..., ge=0)
    total_characters: int = Field(..., ge=0)
    is_text_extractable: bool

    chunk_count: int = Field(..., ge=0)
    stored_chunk_count: int = Field(..., ge=0)

    collection_name: str
    preview_text: str
    sample_chunks: list[DocumentChunk]

    message: str


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class DocumentSearchResult(BaseModel):
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    section_title: str | None = None
    text: str
    char_count: int
    score: float


class DocumentSearchResponse(BaseModel):
    success: bool = Field(default=True)
    query: str
    top_k: int
    result_count: int
    results: list[DocumentSearchResult]


class CitationCard(BaseModel):
    document_id: str
    filename: str
    page_number: int = Field(..., ge=1)
    section_title: str | None = None
    chunk_index: int = Field(..., ge=0)

    # Short text for API/UI citation card display.
    excerpt: str

    # Longer text for LLM grounding.
    # Hidden from API response so the UI remains clean.
    evidence_text: str = Field(exclude=True)

    retrieval_score: float


class DocumentEvidenceRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ConfidenceBreakdown(BaseModel):
    answerability_score: float = Field(..., ge=0.0, le=1.0)
    top_retrieval_score: float = Field(..., ge=0.0, le=1.0)
    average_retrieval_score: float = Field(..., ge=0.0, le=1.0)
    retrieval_margin: float = Field(..., ge=0.0, le=1.0)
    lexical_coverage: float = Field(..., ge=0.0, le=1.0)
    top_chunk_lexical_coverage: float = Field(..., ge=0.0, le=1.0)
    numeric_consistency: float | None = Field(default=None, ge=0.0, le=1.0)
    numeric_mismatch: bool
    query_numeric_claims: list[str]
    evidence_numeric_claims: list[str]
    missing_numeric_claims: list[str]
    scope_risk: bool
    scope_risk_reason: str | None = None
    matched_query_terms: list[str]
    missing_query_terms: list[str]
    direct_support: bool
    decision_reasons: list[str]


class DocumentEvidenceResponse(BaseModel):
    success: bool = Field(default=True)
    query: str
    top_k: int

    answer_ready: bool
    evidence_status: str
    confidence_score: float
    top_retrieval_score: float
    average_retrieval_score: float
    min_retrieval_score: float
    confidence_breakdown: ConfidenceBreakdown | None = None

    citation_count: int
    citations: list[CitationCard]

    fallback_message: str | None = None


class DocumentAnswerRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class DocumentAnswerResponse(BaseModel):
    success: bool = Field(default=True)
    question: str
    answer: str

    answer_ready: bool
    evidence_status: str
    confidence_score: float
    confidence_breakdown: ConfidenceBreakdown | None = None

    citation_count: int
    citations: list[CitationCard]

    llm_provider: str
    model_name: str | None = None
    fallback_used: bool = False
