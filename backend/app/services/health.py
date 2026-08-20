from dataclasses import dataclass
from typing import Literal

from app.db.database import Database
from app.providers.embedding.ollama import OllamaEmbeddingProvider
from app.repositories.vector_repository import VectorRepository

Availability = Literal["ok", "unavailable"]


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    sqlite: Availability
    qdrant: Availability
    ollama: Availability


class HealthService:
    def __init__(
        self,
        database: Database,
        vectors: VectorRepository,
        embeddings: OllamaEmbeddingProvider,
    ) -> None:
        self.database = database
        self.vectors = vectors
        self.embeddings = embeddings

    def check(self) -> HealthSnapshot:
        return HealthSnapshot(
            sqlite=self._safe_check(self.database.ping),
            qdrant=self._safe_check(self.vectors.ping),
            ollama=self._safe_check(self.embeddings.ping),
        )

    @staticmethod
    def _safe_check(check) -> Availability:
        try:
            return "ok" if check() else "unavailable"
        except Exception:
            return "unavailable"
