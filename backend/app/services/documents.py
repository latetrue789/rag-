from pathlib import Path

from app.db.models import DocumentRecord, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository


class DocumentNotFoundError(KeyError):
    """Raised when an active document does not exist."""


class DocumentSourcePresentError(ValueError):
    """Raised when a watched source must be removed before index cleanup."""


class DocumentService:
    def __init__(
        self,
        documents: DocumentRepository,
        vectors: VectorRepository,
        collection: str,
        watched_root: Path | None = None,
    ) -> None:
        self.documents = documents
        self.vectors = vectors
        self.collection = collection
        self.watched_root = watched_root.resolve() if watched_root else None

    def list_documents(self) -> list[DocumentRecord]:
        return self.documents.list_active()

    def delete_document(self, document_id: str) -> DocumentRecord:
        document = self.get_active(document_id)
        if self._is_watched(document) and document.status is not DocumentStatus.MISSING:
            raise DocumentSourcePresentError(document_id)
        self.vectors.delete_document(self.collection, document_id)
        return self.documents.soft_delete(document_id)

    def get_active(self, document_id: str) -> DocumentRecord:
        try:
            document = self.documents.get(document_id)
        except KeyError as error:
            raise DocumentNotFoundError(document_id) from error
        if document.status is DocumentStatus.DELETED:
            raise DocumentNotFoundError(document_id)
        return document

    def _is_watched(self, document: DocumentRecord) -> bool:
        if self.watched_root is None:
            return False
        try:
            Path(document.source_path).resolve().relative_to(self.watched_root)
        except ValueError:
            return False
        return True
