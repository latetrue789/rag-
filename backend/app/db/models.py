from dataclasses import dataclass
from enum import StrEnum


class DocumentStatus(StrEnum):
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"
    MISSING = "missing"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    id: str
    filename: str
    source_path: str
    file_type: str
    content_hash: str
    index_version: str
    status: DocumentStatus
    chunk_count: int
    error_message: str | None
    created_at: str
    updated_at: str
