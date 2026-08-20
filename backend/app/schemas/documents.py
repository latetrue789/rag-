from pydantic import BaseModel

from app.db.models import DocumentStatus


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: DocumentStatus
    chunk_count: int
    error_message: str | None
    updated_at: str


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
