from functools import cached_property

from qdrant_client import QdrantClient

from app.core.config import Settings, get_settings
from app.db.database import Database
from app.providers.embedding.ollama import OllamaEmbeddingProvider
from app.providers.llm.openai_compatible import OpenAICompatibleLLMProvider
from app.repositories.document_repository import DocumentRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.repositories.vector_repository import VectorRepository
from app.services.answering import AnsweringService
from app.services.chunker import Chunker
from app.services.documents import DocumentService
from app.services.evaluation import EvaluationService, LLMJudge
from app.services.folder_sync import FolderSyncService
from app.services.health import HealthService
from app.services.ingestion import IngestionService
from app.services.rag import RagService
from app.services.retrieval import RetrievalService


class ServiceContainer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @cached_property
    def database(self) -> Database:
        database = Database(self.settings.sqlite_file)
        database.initialize()
        return database

    @cached_property
    def documents(self) -> DocumentRepository:
        return DocumentRepository(self.database)

    @cached_property
    def vectors(self) -> VectorRepository:
        client = QdrantClient(url=self.settings.qdrant_url)
        return VectorRepository(client)

    @cached_property
    def embeddings(self) -> OllamaEmbeddingProvider:
        return OllamaEmbeddingProvider(
            base_url=self.settings.embedding_base_url,
            model=self.settings.embedding_model,
        )

    @cached_property
    def ingestion(self) -> IngestionService:
        return IngestionService(
            documents=self.documents,
            vectors=self.vectors,
            embeddings=self.embeddings,
            chunker=Chunker(
                chunk_size=self.settings.chunk_size,
                overlap=self.settings.chunk_overlap,
            ),
            collection=self.settings.qdrant_collection,
            embedding_batch_size=self.settings.embedding_batch_size,
        )

    @cached_property
    def folder_sync(self) -> FolderSyncService:
        return FolderSyncService(
            root=self.settings.documents_directory,
            ingestion=self.ingestion,
            documents=self.documents,
            stable_seconds=self.settings.document_stable_seconds,
            max_size_mb=self.settings.document_max_size_mb,
        )

    @cached_property
    def llm(self) -> OpenAICompatibleLLMProvider | None:
        if not self.settings.llm_configured:
            return None
        api_key = self.settings.llm_api_key
        assert api_key is not None
        return OpenAICompatibleLLMProvider(
            base_url=self.settings.llm_base_url,
            api_key=api_key.get_secret_value(),
            model=self.settings.llm_model,
        )

    @cached_property
    def retrieval(self) -> RetrievalService:
        return RetrievalService(
            embeddings=self.embeddings,
            vectors=self.vectors,
            collection=self.settings.qdrant_collection,
            top_k=self.settings.retrieval_top_k,
            score_threshold=self.settings.retrieval_score_threshold,
        )

    @cached_property
    def rag(self) -> RagService:
        return RagService(self.retrieval, AnsweringService(self.llm))

    @cached_property
    def document_service(self) -> DocumentService:
        return DocumentService(
            self.documents,
            self.vectors,
            self.settings.qdrant_collection,
            watched_root=self.settings.documents_directory,
        )

    @cached_property
    def health(self) -> HealthService:
        return HealthService(self.database, self.vectors, self.embeddings)

    @cached_property
    def evaluations(self) -> EvaluationRepository:
        return EvaluationRepository(self.database)

    @cached_property
    def evaluation(self) -> EvaluationService:
        judge = LLMJudge(self.llm) if self.llm is not None else None
        return EvaluationService(
            rag=self.rag,
            judge=judge,
            repository=self.evaluations,
            report_directory=self.settings.evaluation_report_directory,
        )
