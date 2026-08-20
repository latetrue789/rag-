from dataclasses import dataclass, field
from time import perf_counter

from app.providers.base import EmbeddingProvider, LLMProvider
from app.repositories.vector_repository import SearchResult, VectorRepository


class RetrievalUnavailableError(RuntimeError):
    """Raised when the vector database cannot execute a search."""


@dataclass(frozen=True, slots=True)
class Source:
    source_id: str
    document_id: str
    filename: str
    file_type: str
    text: str
    score: float
    chunk_index: int
    title: str | None = None
    page: int | None = None


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    query: str
    sources: list[Source]
    rewritten: bool = False
    timings_ms: dict[str, float] = field(default_factory=dict)


class RetrievalService:
    def __init__(
        self,
        *,
        embeddings: EmbeddingProvider,
        vectors: VectorRepository,
        collection: str,
        top_k: int = 5,
        score_threshold: float = 0.55,
        rewriter: LLMProvider | None = None,
    ) -> None:
        self.embeddings = embeddings
        self.vectors = vectors
        self.collection = collection
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.rewriter = rewriter

    def retrieve(self, question: str) -> RetrievalResult:
        started = perf_counter()
        results, embedding_ms, search_ms = self._search(question)
        query = question
        rewritten = False
        if not results and self.rewriter is not None:
            query = self._rewrite(question)
            if query and query != question:
                rewritten = True
                results, retry_embedding, retry_search = self._search(query)
                embedding_ms += retry_embedding
                search_ms += retry_search
        return RetrievalResult(
            query=query,
            sources=self.to_sources(results),
            rewritten=rewritten,
            timings_ms={
                "embedding": round(embedding_ms, 2),
                "retrieval": round(search_ms, 2),
                "total": round((perf_counter() - started) * 1000, 2),
            },
        )

    def _search(self, query: str) -> tuple[list[SearchResult], float, float]:
        embedding_started = perf_counter()
        vector = self.embeddings.embed([query])[0]
        embedding_ms = (perf_counter() - embedding_started) * 1000
        retrieval_started = perf_counter()
        try:
            results = self.vectors.query(
                self.collection,
                vector,
                limit=self.top_k,
                score_threshold=self.score_threshold,
            )
        except Exception as error:
            raise RetrievalUnavailableError("向量检索服务暂时不可用") from error
        search_ms = (perf_counter() - retrieval_started) * 1000
        return results, embedding_ms, search_ms

    def _rewrite(self, question: str) -> str:
        return self.rewriter.complete(
            [
                {
                    "role": "system",
                    "content": "将问题改写为便于检索求职资料的单句查询，只返回改写结果。",
                },
                {"role": "user", "content": question},
            ]
        ).strip()

    @staticmethod
    def to_sources(results: list[SearchResult]) -> list[Source]:
        return [
            Source(
                source_id=f"S{index}",
                document_id=item.document_id,
                filename=item.filename,
                file_type=item.file_type,
                text=item.text,
                score=item.score,
                chunk_index=item.chunk_index,
                title=item.title,
                page=item.page,
            )
            for index, item in enumerate(results, start=1)
        ]
