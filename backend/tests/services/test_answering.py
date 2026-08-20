from app.providers.base import ProviderUnavailableError
from app.repositories.vector_repository import SearchResult
from app.services.answering import AnsweringService
from app.services.retrieval import RetrievalResult, RetrievalService


class FakeEmbeddingProvider:
    model_name = "fake"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class FakeVectorRepository:
    def __init__(self, responses: list[list[SearchResult]]) -> None:
        self.responses = responses
        self.queries: list[tuple[str, int, float | None]] = []

    def query(
        self,
        collection: str,
        vector: list[float],
        *,
        limit: int = 5,
        score_threshold: float | None = None,
    ) -> list[SearchResult]:
        self.queries.append((collection, limit, score_threshold))
        return self.responses.pop(0)


class FakeLLM:
    model_name = "fake-llm"

    def __init__(self, replies: list[str | Exception]) -> None:
        self.replies = replies
        self.calls = 0

    def complete(self, messages):
        reply = self.replies[self.calls]
        self.calls += 1
        if isinstance(reply, Exception):
            raise reply
        return reply


def result(text: str = "JD 要求掌握 FastAPI", score: float = 0.88) -> SearchResult:
    return SearchResult(
        chunk_id="chunk-1",
        document_id="doc-1",
        filename="ai-jd.md",
        file_type="md",
        text=text,
        chunk_index=0,
        score=score,
        title="技能要求",
    )


def test_retrieval_uses_top_k_threshold_and_stable_source_ids() -> None:
    vectors = FakeVectorRepository([[result(), result("RAG 要求", 0.8)]])
    service = RetrievalService(
        embeddings=FakeEmbeddingProvider(),
        vectors=vectors,
        collection="chunks",
        top_k=4,
        score_threshold=0.6,
    )

    retrieval = service.retrieve("岗位要求什么？")

    assert vectors.queries == [("chunks", 4, 0.6)]
    assert [source.source_id for source in retrieval.sources] == ["S1", "S2"]
    assert retrieval.sources[0].filename == "ai-jd.md"


def test_retrieval_rewrites_at_most_once_when_evidence_is_missing() -> None:
    vectors = FakeVectorRepository([[], [result()]])
    rewriter = FakeLLM(["AI 应用开发岗位 FastAPI 技能要求"])
    service = RetrievalService(
        embeddings=FakeEmbeddingProvider(),
        vectors=vectors,
        collection="chunks",
        rewriter=rewriter,
    )

    retrieval = service.retrieve("我要学什么？")

    assert retrieval.rewritten is True
    assert retrieval.query == "AI 应用开发岗位 FastAPI 技能要求"
    assert len(vectors.queries) == 2
    assert rewriter.calls == 1


def test_answering_returns_grounded_answer_with_sources() -> None:
    llm = FakeLLM(["该岗位要求掌握 FastAPI。[S1]"])
    retrieval = RetrievalResult(query="技能", sources=RetrievalService.to_sources([result()]))

    response = AnsweringService(llm).answer("岗位要求什么？", retrieval)

    assert response.grounded is True
    assert response.answer.endswith("[S1]")
    assert response.sources[0].source_id == "S1"
    assert llm.calls == 1


def test_answering_repairs_invalid_citation_once_then_falls_back() -> None:
    llm = FakeLLM(["需要 FastAPI。[S9]", "还是错误。[S8]"])
    retrieval = RetrievalResult(query="技能", sources=RetrievalService.to_sources([result()]))

    response = AnsweringService(llm).answer("岗位要求什么？", retrieval)

    assert llm.calls == 2
    assert response.grounded is False
    assert "无法生成可靠引用" in response.answer
    assert response.sources


def test_answering_skips_llm_without_evidence_and_keeps_sources_on_llm_failure() -> None:
    llm = FakeLLM([ProviderUnavailableError("offline")])
    service = AnsweringService(llm)

    empty = service.answer("岗位要求什么？", RetrievalResult(query="技能", sources=[]))
    failed = service.answer(
        "岗位要求什么？",
        RetrievalResult(query="技能", sources=RetrievalService.to_sources([result()])),
    )

    assert empty.grounded is False
    assert "证据不足" in empty.answer
    assert failed.grounded is False
    assert failed.sources
    assert "暂时无法生成答案" in failed.answer
