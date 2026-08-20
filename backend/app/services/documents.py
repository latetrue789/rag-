from app.db.models import DocumentRecord, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository


class DocumentNotFoundError(KeyError):
    """Raised when an active document does not exist."""


class DocumentService:
    def __init__(
        self,
        documents: DocumentRepository,
        vectors: VectorRepository,
        collection: str,
    ) -> None:
        self.documents = documents
        self.vectors = vectors
        self.collection = collection

    def list_documents(self) -> list[DocumentRecord]:
        return self.documents.list_active()

    def delete_document(self, document_id: str) -> DocumentRecord:
        try:
            document = self.documents.get(document_id)
        except KeyError as error:
            raise DocumentNotFoundError(document_id) from error
        if document.status is DocumentStatus.DELETED:
            raise DocumentNotFoundError(document_id)
        self.vectors.delete_document(self.collection, document_id)
        return self.documents.soft_delete(document_id)
