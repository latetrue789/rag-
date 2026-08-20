from pathlib import Path

from qdrant_client import QdrantClient

from app.db.database import Database
from app.repositories.document_repository import DocumentRepository
from app.repositories.vector_repository import VectorRepository
from app.services.answering import AnsweringService
from app.services.chunker import Chunker
from app.services.ingestion import IngestionAction, IngestionService
from app.services.rag import RagService
from app.services.retrieval import RetrievalService


class KeywordEmbedding:
    model_name = "keyword-test-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [
            [float("FastAPI" in text), float("RAG" in text)]
            for text in texts
        ]


class CitingLLM:
    model_name = "citing-test-llm"

    def complete(self, messages) -> str:
        return "岗位资料要求掌握 FastAPI 和 RAG。[S1]"


def test_document_to_grounded_answer_pipeline(tmp_path: Path) -> None:
    source = tmp_path / "ai-job.md"
    source.write_text(
        "# 技能要求\n\n岗位要求掌握 FastAPI，并能完成 RAG 检索链路。",
        encoding="utf-8",
    )
    database = Database(tmp_path / "app.db")
    database.initialize()
    documents = DocumentRepository(database)
    vectors = VectorRepository(QdrantClient(location=":memory:"))
    embeddings = KeywordEmbedding()
    ingestion = IngestionService(
        documents=documents,
        vectors=vectors,
        embeddings=embeddings,
        chunker=Chunker(chunk_size=200, overlap=20),
        collection="e2e_chunks",
    )

    indexed = ingestion.ingest(source)
    rag = RagService(
        RetrievalService(
            embeddings=embeddings,
            vectors=vectors,
            collection="e2e_chunks",
            score_threshold=0.1,
        ),
        AnsweringService(CitingLLM()),
    )
    response = rag.ask("岗位要求哪些 FastAPI 和 RAG 技能？")

    assert indexed.action is IngestionAction.INDEXED
    assert response.grounded is True
    assert response.sources[0].filename == "ai-job.md"
    assert response.answer.endswith("[S1]")
