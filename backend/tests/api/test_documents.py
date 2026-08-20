import asyncio
from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient

from app.db.models import DocumentRecord, DocumentStatus
from app.main import create_app
from app.services.documents import DocumentNotFoundError


def record() -> DocumentRecord:
    return DocumentRecord(
        id="doc-1",
        filename="ai-jd.md",
        source_path="D:/private/ai-jd.md",
        file_type="md",
        content_hash="hash",
        index_version="bge-m3",
        status=DocumentStatus.INDEXED,
        chunk_count=3,
        error_message=None,
        created_at="2026-08-20T00:00:00+00:00",
        updated_at="2026-08-20T00:00:00+00:00",
    )


class FakeDocumentService:
    def __init__(self, missing: bool = False) -> None:
        self.missing = missing

    def list_documents(self) -> list[DocumentRecord]:
        return [record()]

    def delete_document(self, document_id: str) -> DocumentRecord:
        if self.missing:
            raise DocumentNotFoundError(document_id)
        return record()


async def request(app, method: str, path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path)


def test_list_documents_omits_private_path_and_hash() -> None:
    app = create_app(SimpleNamespace(document_service=FakeDocumentService()))
    response = asyncio.run(request(app, "GET", "/api/v1/documents"))

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["filename"] == "ai-jd.md"
    assert "source_path" not in response.text
    assert "content_hash" not in response.text


def test_delete_document_returns_no_content_or_not_found() -> None:
    ok_app = create_app(SimpleNamespace(document_service=FakeDocumentService()))
    missing_app = create_app(
        SimpleNamespace(document_service=FakeDocumentService(missing=True))
    )

    assert asyncio.run(request(ok_app, "DELETE", "/api/v1/documents/doc-1")).status_code == 204
    assert (
        asyncio.run(request(missing_app, "DELETE", "/api/v1/documents/missing")).status_code
        == 404
    )
