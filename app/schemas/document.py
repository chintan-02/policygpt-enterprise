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