from qdrant_client import QdrantClient

from app.repositories.vector_repository import VectorRepository
from app.services.chunker import Chunk


def test_upsert_query_and_delete_document() -> None:
    repository = VectorRepository(QdrantClient(location=":memory:"))
    collection = "test_chunks"
    chunks = [
        Chunk(text="FastAPI 用于构建后端接口", index=0, title="岗位技能"),
        Chunk(text="RAG 回答需要提供来源引用", index=1, page=2),
    ]

    repository.ensure_collection(collection, dimension=3)
    repository.upsert_chunks(
        collection=collection,
        document_id="doc-1",
        filename="ai-jd.md",
        file_type="md",
        content_hash="hash-1",
        chunks=chunks,
        vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    )

    results = repository.query(collection, [1.0, 0.0, 0.0], limit=2)

    assert len(results) == 2
    assert results[0].document_id == "doc-1"
    assert results[0].filename == "ai-jd.md"
    assert results[0].text == "FastAPI 用于构建后端接口"
    assert results[0].title == "岗位技能"
    assert results[0].score > results[1].score

    repository.delete_document(collection, "doc-1")
    assert repository.query(collection, [1.0, 0.0, 0.0], limit=2) == []


def test_ensure_collection_rejects_dimension_mismatch() -> None:
    repository = VectorRepository(QdrantClient(location=":memory:"))
    repository.ensure_collection("test_chunks", dimension=3)

    try:
        repository.ensure_collection("test_chunks", dimension=2)
    except ValueError as error:
        assert "dimension" in str(error)
    else:
        raise AssertionError("Expected dimension mismatch to fail")
