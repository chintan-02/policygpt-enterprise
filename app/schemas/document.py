from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    success: bool = Field(default=True)
    document_id: str
    filename: str
    content_type: str
    size_bytes: int
    message: str