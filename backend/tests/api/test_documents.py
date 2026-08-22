import asyncio
from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient

from app.db.models import DocumentRecord, DocumentStatus
from app.main import create_app
from app.services.documents import (
    DocumentNotFoundError,
    DocumentSourcePresentError,
)
from app.services.folder_sync import FolderSyncResult


def record(status: DocumentStatus = DocumentStatus.INDEXED) -> DocumentRecord:
    return DocumentRecord(
        id="doc-1",
        filename="ai-jd.md",
        source_path="D:/private/ai-jd.md",
        file_type="md",
        content_hash="hash",
        index_version="bge-m3",
        status=status,
        chunk_count=3,
        error_message=None,
        created_at="2026-08-20T00:00:00+00:00",
        updated_at="2026-08-20T00:00:00+00:00",
    )


class FakeDocumentService:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def list_documents(self) -> list[DocumentRecord]:
        return [record()]

    def delete_document(self, document_id: str) -> DocumentRecord:
        if self.error is not None:
            raise self.error
        return record(DocumentStatus.DELETED)


class FakeFolderSync:
    is_scanning = False
    last_result = FolderSyncResult(skipped=2, scanned_at="2026-08-22T00:00:00+00:00")

    def scan(self) -> FolderSyncResult:
        self.last_result = FolderSyncResult(indexed=1, scanned_at="2026-08-22T00:01:00+00:00")
        return self.last_result

    def retry(self, document_id: str) -> DocumentRecord:
        return record()


def container(document_service: FakeDocumentService | None = None):
    return SimpleNamespace(
        document_service=document_service or FakeDocumentService(),
        folder_sync=FakeFolderSync(),
        settings=SimpleNamespace(document_scan_interval_seconds=60),
    )


async def request(app, method: str, path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path)


def test_list_documents_omits_private_path_and_hash() -> None:
    app = create_app(container())
    response = asyncio.run(request(app, "GET", "/api/v1/documents"))

    assert response.status_code == 200
    assert response.json()["items"][0]["filename"] == "ai-jd.md"
    assert "source_path" not in response.text
    assert "content_hash" not in response.text


def test_scan_status_uses_public_relative_directory_and_manual_scan() -> None:
    app = create_app(container())

    status_response = asyncio.run(request(app, "GET", "/api/v1/documents/scan"))
    scan_response = asyncio.run(request(app, "POST", "/api/v1/documents/scan"))

    assert status_response.status_code == 200
    assert status_response.json()["directory"] == "data/documents/"
    assert "D:/" not in status_response.text
    assert scan_response.json()["indexed"] == 1


def test_delete_document_returns_no_content_or_not_found() -> None:
    ok_app = create_app(container())
    missing_app = create_app(
        container(FakeDocumentService(DocumentNotFoundError("missing")))
    )

    assert asyncio.run(request(ok_app, "DELETE", "/api/v1/documents/doc-1")).status_code == 204
    assert (
        asyncio.run(request(missing_app, "DELETE", "/api/v1/documents/missing")).status_code
        == 404
    )


def test_watched_source_must_be_removed_before_cleanup() -> None:
    app = create_app(
        container(FakeDocumentService(DocumentSourcePresentError("doc-1")))
    )

    response = asyncio.run(request(app, "DELETE", "/api/v1/documents/doc-1"))

    assert response.status_code == 409
    assert "先从 data/documents/ 移除" in response.json()["detail"]
