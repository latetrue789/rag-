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


class DocumentScanSummaryResponse(BaseModel):
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    waiting: int = 0
    missing: int = 0
    oversized: int = 0
    busy: bool = False
    scanned_at: str | None = None


class DocumentScanStatusResponse(BaseModel):
    directory: str
    subdirectories: list[str]
    interval_seconds: int
    scanning: bool
    last_scan: DocumentScanSummaryResponse | None
