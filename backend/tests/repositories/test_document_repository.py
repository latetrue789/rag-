from pathlib import Path

from app.db.database import Database
from app.db.models import DocumentStatus
from app.repositories.document_repository import DocumentRepository


def create_repository(tmp_path: Path) -> DocumentRepository:
    database = Database(tmp_path / "documents.db")
    database.initialize()
    return DocumentRepository(database)


def test_create_and_find_document_by_hash(tmp_path: Path) -> None:
    repository = create_repository(tmp_path)

    document = repository.create(
        filename="岗位说明.md",
        source_path="D:/private/岗位说明.md",
        file_type="markdown",
        content_hash="abc123",
        index_version="bge-m3-v1",
    )

    found = repository.get_by_hash("abc123")
    assert found == document
    assert found.status is DocumentStatus.PENDING


def test_mark_document_indexed_and_failed(tmp_path: Path) -> None:
    repository = create_repository(tmp_path)
    indexed = repository.create("a.txt", "a.txt", "text", "hash-a", "v1")
    failed = repository.create("b.pdf", "b.pdf", "pdf", "hash-b", "v1")

    repository.mark_indexed(indexed.id, chunk_count=4)
    repository.mark_failed(failed.id, "PDF 中没有可提取文字")

    records = {record.id: record for record in repository.list_all()}
    assert records[indexed.id].status is DocumentStatus.INDEXED
    assert records[indexed.id].chunk_count == 4
    assert records[failed.id].status is DocumentStatus.FAILED
    assert records[failed.id].error_message == "PDF 中没有可提取文字"


def test_soft_delete_hides_document_from_active_path_lookup(tmp_path: Path) -> None:
    repository = create_repository(tmp_path)
    document = repository.create("a.txt", "a.txt", "text", "hash-a", "v1")

    repository.soft_delete(document.id)

    assert repository.get_active_by_source_path("a.txt") is None
    assert repository.get(document.id).status is DocumentStatus.DELETED
