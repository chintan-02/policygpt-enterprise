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
    excerpt: str
    retrieval_score: float


class DocumentEvidenceRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class DocumentEvidenceResponse(BaseModel):
    success: bool = Field(default=True)
    query: str
    top_k: int

    answer_ready: bool
    evidence_status: str
    confidence_score: float
    min_retrieval_score: float

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

    citation_count: int
    citations: list[CitationCard]

    llm_provider: str
    model_name: str | None = None
    fallback_used: bool = False