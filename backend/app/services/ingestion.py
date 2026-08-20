from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.db.models import DocumentRecord
from app.providers.base import EmbeddingProvider
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chunker import Chunker
from app.services.document_hasher import sha256_file
from app.services.parsing import parser_for


class IngestionAction(StrEnum):
    INDEXED = "indexed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    action: IngestionAction
    document: DocumentRecord
    chunk_count: int = 0
    message: str | None = None


class IngestionService:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        vectors: VectorRepository,
        embeddings: EmbeddingProvider,
        chunker: Chunker,
        collection: str,
    ) -> None:
        self.documents = documents
        self.vectors = vectors
        self.embeddings = embeddings
        self.chunker = chunker
        self.collection = collection

    def ingest(self, path: Path) -> IngestionOutcome:
        source = path.resolve()
        content_hash = sha256_file(source)
        duplicate = self.documents.get_by_hash(content_hash)
        if duplicate and duplicate.status.value == "indexed":
            return IngestionOutcome(IngestionAction.SKIPPED, duplicate)

        previous = self.documents.get_active_by_source_path(str(source))
        document = self.documents.create(
            filename=source.name,
            source_path=str(source),
            file_type=source.suffix.lower().lstrip("."),
            content_hash=content_hash,
            index_version=self.embeddings.model_name,
        )
        try:
            sections = parser_for(source).parse(source)
            chunks = self.chunker.split(sections)
            if not chunks:
                raise ValueError("文档中没有可索引的文字")
            vectors = self.embeddings.embed([chunk.text for chunk in chunks])
            if len(vectors) != len(chunks) or not vectors or not vectors[0]:
                raise ValueError("Embedding provider returned invalid vectors")
            self.vectors.ensure_collection(self.collection, len(vectors[0]))
            self.vectors.upsert_chunks(
                collection=self.collection,
                document_id=document.id,
                filename=document.filename,
                file_type=document.file_type,
                content_hash=document.content_hash,
                chunks=chunks,
                vectors=vectors,
            )
            if previous is not None:
                self.vectors.delete_document(self.collection, previous.id)
                self.documents.soft_delete(previous.id)
            indexed = self.documents.mark_indexed(document.id, len(chunks))
            return IngestionOutcome(IngestionAction.INDEXED, indexed, len(chunks))
        except Exception as error:
            failed = self.documents.mark_failed(document.id, str(error))
            return IngestionOutcome(
                IngestionAction.FAILED,
                failed,
                message=str(error),
            )

    def ingest_many(self, paths: list[Path]) -> list[IngestionOutcome]:
        return [self.ingest(path) for path in paths]
