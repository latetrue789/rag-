import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from app.db.database import Database
from app.db.models import DocumentRecord, DocumentStatus


class DocumentRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        filename: str,
        source_path: str,
        file_type: str,
        content_hash: str,
        index_version: str,
    ) -> DocumentRecord:
        document_id = str(uuid4())
        now = self._now()
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, filename, source_path, file_type, content_hash,
                    index_version, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    filename,
                    source_path,
                    file_type,
                    content_hash,
                    index_version,
                    DocumentStatus.PENDING,
                    now,
                    now,
                ),
            )
        return self.get(document_id)

    def get(self, document_id: str) -> DocumentRecord:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Document not found: {document_id}")
        return self._from_row(row)

    def get_by_hash(self, content_hash: str) -> DocumentRecord | None:
        return self._find_active("content_hash", content_hash)

    def get_active_by_source_path(self, source_path: str) -> DocumentRecord | None:
        return self._find_active("source_path", source_path)

    def list_all(self) -> list[DocumentRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY created_at DESC",
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def list_active(self) -> list[DocumentRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM documents
                WHERE status != ?
                ORDER BY updated_at DESC
                """,
                (DocumentStatus.DELETED,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def mark_indexed(self, document_id: str, chunk_count: int) -> DocumentRecord:
        return self._update_status(
            document_id,
            DocumentStatus.INDEXED,
            chunk_count=chunk_count,
            error_message=None,
        )

    def mark_failed(self, document_id: str, error_message: str) -> DocumentRecord:
        return self._update_status(
            document_id,
            DocumentStatus.FAILED,
            chunk_count=0,
            error_message=error_message,
        )

    def soft_delete(self, document_id: str) -> DocumentRecord:
        current = self.get(document_id)
        return self._update_status(
            document_id,
            DocumentStatus.DELETED,
            chunk_count=current.chunk_count,
            error_message=current.error_message,
        )

    def _find_active(self, column: str, value: str) -> DocumentRecord | None:
        if column not in {"content_hash", "source_path"}:
            raise ValueError(f"Unsupported lookup column: {column}")
        with self.database.connect() as connection:
            row = connection.execute(
                f"""
                SELECT * FROM documents
                WHERE {column} = ? AND status != ?
                ORDER BY updated_at DESC LIMIT 1
                """,
                (value, DocumentStatus.DELETED),
            ).fetchone()
        return self._from_row(row) if row else None

    def _update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        *,
        chunk_count: int,
        error_message: str | None,
    ) -> DocumentRecord:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE documents
                SET status = ?, chunk_count = ?, error_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, chunk_count, error_message, self._now(), document_id),
            )
        if cursor.rowcount == 0:
            raise KeyError(f"Document not found: {document_id}")
        return self.get(document_id)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            id=row["id"],
            filename=row["filename"],
            source_path=row["source_path"],
            file_type=row["file_type"],
            content_hash=row["content_hash"],
            index_version=row["index_version"],
            status=DocumentStatus(row["status"]),
            chunk_count=row["chunk_count"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
