import asyncio
from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.services.rag import RagResponse
from app.services.retrieval import Source


class FakeRagService:
    def ask(self, question: str) -> RagResponse:
        assert question == "岗位需要哪些技能？"
        return RagResponse(
            answer="岗位要求掌握 FastAPI。[S1]",
            sources=[
                Source(
                    source_id="S1",
                    document_id="doc-1",
                    filename="ai-jd.md",
                    file_type="md",
                    text="掌握 FastAPI",
                    score=0.88,
                    chunk_index=0,
                    title="技能要求",
                )
            ],
            grounded=True,
            trace_id="trace-1",
            timings_ms={"total": 12.3},
            rewritten=False,
        )


def test_ask_returns_grounded_answer_and_citation_sources() -> None:
    app = create_app(SimpleNamespace(rag=FakeRagService()))

    async def request():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/api/v1/ask",
                json={"question": "岗位需要哪些技能？"},
            )

    response = asyncio.run(request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is True
    assert payload["sources"][0]["source_id"] == "S1"
    assert payload["trace_id"] == "trace-1"


def test_ask_rejects_too_short_question() -> None:
    app = create_app(SimpleNamespace(rag=FakeRagService()))

    async def request():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post("/api/v1/ask", json={"question": "?"})

    response = asyncio.run(request())
    assert response.status_code == 422
