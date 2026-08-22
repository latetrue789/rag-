from pathlib import Path

from qdrant_client import QdrantClient

from app.db.database import Database
from app.db.models import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chunker import Chunker
from app.services.folder_sync import FolderSyncService
from app.services.ingestion import IngestionService


class RecordingEmbeddingProvider:
    model_name = "fake-embedding"

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[float("RAG" in text), 0.5, 0.25] for text in texts]


def create_sync(
    tmp_path: Path,
    *,
    stable_seconds: int = 0,
    batch_size: int = 32,
) -> tuple[FolderSyncService, DocumentRepository, RecordingEmbeddingProvider]:
    database = Database(tmp_path / "documents.db")
    database.initialize()
    documents = DocumentRepository(database)
    vectors = VectorRepository(QdrantClient(location=":memory:"))
    embeddings = RecordingEmbeddingProvider()
    ingestion = IngestionService(
        documents=documents,
        vectors=vectors,
        embeddings=embeddings,
        chunker=Chunker(chunk_size=12, overlap=2),
        collection="test_chunks",
        embedding_batch_size=batch_size,
    )
    sync = FolderSyncService(
        root=tmp_path / "data" / "documents",
        ingestion=ingestion,
        documents=documents,
        stable_seconds=stable_seconds,
        max_size_mb=1,
    )
    return sync, documents, embeddings


def test_scan_creates_format_directories_and_indexes_recursively(tmp_path: Path) -> None:
    sync, documents, _ = create_sync(tmp_path)
    sync.ensure_directories()
    source = sync.root / "md" / "岗位.md"
    source.write_text("# 岗位要求\n\n需要 RAG 与 FastAPI。", encoding="utf-8")

    result = sync.scan()

    assert sorted(path.name for path in sync.root.iterdir()) == ["md", "pdf", "txt"]
    assert result.indexed == 1
    assert documents.list_active()[0].status is DocumentStatus.INDEXED


def test_removed_file_is_marked_missing_and_restored_without_embedding(
    tmp_path: Path,
) -> None:
    sync, documents, embeddings = create_sync(tmp_path)
    sync.ensure_directories()
    source = sync.root / "txt" / "notes.txt"
    source.write_text("RAG 面试题", encoding="utf-8")
    sync.scan()
    call_count = len(embeddings.calls)

    source.unlink()
    missing = sync.scan()
    assert missing.missing == 1
    assert documents.list_active()[0].status is DocumentStatus.MISSING

    source.write_text("RAG 面试题", encoding="utf-8")
    restored = sync.scan()
    assert restored.skipped == 1
    assert documents.list_active()[0].status is DocumentStatus.INDEXED
    assert len(embeddings.calls) == call_count


def test_unstable_file_waits_and_failed_file_is_not_retried(tmp_path: Path) -> None:
    sync, documents, _ = create_sync(tmp_path, stable_seconds=10)
    sync.ensure_directories()
    pending = sync.root / "pdf" / "copying.pdf"
    pending.write_bytes(b"not a pdf")

    first = sync.scan()
    assert first.waiting == 1
    assert documents.list_active() == []

    sync.stable_seconds = 0
    failed = sync.scan()
    repeated = sync.scan()
    assert failed.failed == 1
    assert repeated.skipped == 1
    assert len(documents.list_active()) == 1


def test_embeddings_are_sent_in_bounded_batches(tmp_path: Path) -> None:
    sync, _, embeddings = create_sync(tmp_path, batch_size=2)
    sync.ensure_directories()
    source = sync.root / "txt" / "long.txt"
    source.write_text("RAG FastAPI " * 30, encoding="utf-8")

    sync.scan()

    assert len(embeddings.calls) > 1
    assert all(len(batch) <= 2 for batch in embeddings.calls)
