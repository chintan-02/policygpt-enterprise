from pydantic import BaseModel, Field


class ExtractedPageText(BaseModel):
    page_number: int = Field(..., ge=1)
    text: str
    char_count: int = Field(..., ge=0)


class PDFExtractionResult(BaseModel):
    page_count: int = Field(..., ge=0)
    total_characters: int = Field(..., ge=0)
    pages: list[ExtractedPageText]


class DocumentExtractionResponse(BaseModel):
    success: bool = Field(default=True)
    document_id: str
    filename: str
    content_type: str
    size_bytes: int = Field(..., ge=0)
    page_count: int = Field(..., ge=0)
    total_characters: int = Field(..., ge=0)
    is_text_extractable: bool
    preview_text: str
    pages: list[ExtractedPageText]
    message: str