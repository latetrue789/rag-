from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from app.services.chunker import Chunk


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk_id: str
    document_id: str
    filename: str
    file_type: str
    text: str
    chunk_index: int
    score: float
    title: str | None = None
    page: int | None = None


class VectorRepository:
    def __init__(self, client: QdrantClient) -> None:
        self.client = client

    def ping(self) -> bool:
        self.client.get_collections()
        return True

    def ensure_collection(self, collection: str, dimension: int) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        if self.client.collection_exists(collection):
            info = self.client.get_collection(collection)
            vectors = info.config.params.vectors
            existing_size = getattr(vectors, "size", None)
            if existing_size != dimension:
                raise ValueError(
                    f"Collection vector dimension is {existing_size}, expected {dimension}"
                )
            return
        self.client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_chunks(
        self,
        *,
        collection: str,
        document_id: str,
        filename: str,
        file_type: str,
        content_hash: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        points = [
            models.PointStruct(
                id=str(uuid5(NAMESPACE_URL, f"{document_id}:{chunk.index}")),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "filename": filename,
                    "file_type": file_type,
                    "content_hash": content_hash,
                    "text": chunk.text,
                    "chunk_index": chunk.index,
                    "title": chunk.title,
                    "page": chunk.page,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            self.client.upsert(collection_name=collection, points=points, wait=True)

    def query(
        self,
        collection: str,
        vector: list[float],
        *,
        limit: int = 5,
        score_threshold: float | None = None,
    ) -> list[SearchResult]:
        if not self.client.collection_exists(collection):
            return []
        response = self.client.query_points(
            collection_name=collection,
            query=vector,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
        return [self._from_point(point) for point in response.points]

    def delete_document(self, collection: str, document_id: str) -> None:
        if not self.client.collection_exists(collection):
            return
        self.client.delete(
            collection_name=collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
            wait=True,
        )

    @staticmethod
    def _from_point(point: models.ScoredPoint) -> SearchResult:
        payload = point.payload or {}
        return SearchResult(
            chunk_id=str(point.id),
            document_id=str(payload["document_id"]),
            filename=str(payload["filename"]),
            file_type=str(payload["file_type"]),
            text=str(payload["text"]),
            chunk_index=int(payload["chunk_index"]),
            score=float(point.score),
            title=str(payload["title"]) if payload.get("title") else None,
            page=int(payload["page"]) if payload.get("page") is not None else None,
        )
