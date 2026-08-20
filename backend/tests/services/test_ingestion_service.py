from pathlib import Path

from qdrant_client import QdrantClient

from app.db.database import Database
from app.db.models import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chunker import Chunker
from app.services.ingestion import IngestionAction, IngestionService


class FakeEmbeddingProvider:
    model_name = "fake-embedding"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [
            [float("FastAPI" in text), float("RAG" in text), 0.5]
            for text in texts
        ]


def create_service(tmp_path: Path) -> tuple[IngestionService, DocumentRepository]:
    database = Database(tmp_path / "documents.db")
    database.initialize()
    documents = DocumentRepository(database)
    vectors = VectorRepository(QdrantClient(location=":memory:"))
    service = IngestionService(
        documents=documents,
        vectors=vectors,
        embeddings=FakeEmbeddingProvider(),
        chunker=Chunker(chunk_size=30, overlap=5),
        collection="test_chunks",
    )
    return service, documents


def test_ingest_document_and_skip_unchanged_duplicate(tmp_path: Path) -> None:
    service, documents = create_service(tmp_path)
    source = tmp_path / "岗位.md"
    source.write_text("# 后端技能\n\nFastAPI 和 RAG 都是岗位要求。", encoding="utf-8")

    first = service.ingest(source)
    duplicate = service.ingest(source)

    assert first.action is IngestionAction.INDEXED
    assert first.chunk_count > 0
    assert documents.get(first.document.id).status is DocumentStatus.INDEXED
    assert duplicate.action is IngestionAction.SKIPPED
    assert duplicate.document.id == first.document.id
    assert len(documents.list_all()) == 1


def test_ingest_changed_file_replaces_previous_version(tmp_path: Path) -> None:
    service, documents = create_service(tmp_path)
    source = tmp_path / "notes.txt"
    source.write_text("FastAPI", encoding="utf-8")
    first = service.ingest(source)

    source.write_text("FastAPI 与 RAG", encoding="utf-8")
    second = service.ingest(source)

    assert second.action is IngestionAction.INDEXED
    assert second.document.id != first.document.id
    assert documents.get(first.document.id).status is DocumentStatus.DELETED
    assert documents.get(second.document.id).status is DocumentStatus.INDEXED


def test_ingest_failure_is_recorded_and_batch_continues(tmp_path: Path) -> None:
    service, documents = create_service(tmp_path)
    valid = tmp_path / "valid.txt"
    invalid = tmp_path / "invalid.csv"
    valid.write_text("RAG 学习资料", encoding="utf-8")
    invalid.write_text("unsupported", encoding="utf-8")

    outcomes = service.ingest_many([invalid, valid])

    assert [outcome.action for outcome in outcomes] == [
        IngestionAction.FAILED,
        IngestionAction.INDEXED,
    ]
    failed = documents.get(outcomes[0].document.id)
    assert failed.status is DocumentStatus.FAILED
    assert "不支持" in (failed.error_message or "")
