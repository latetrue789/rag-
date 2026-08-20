from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="RAG_",
        extra="ignore",
    )

    app_name: str = "RAG 求职知识库"
    app_version: str = "0.1.0"
    environment: str = "development"
    llm_base_url: str = ""
    llm_api_key: SecretStr | None = None
    llm_model: str = ""
    embedding_base_url: str = "http://127.0.0.1:11434"
    embedding_model: str = "bge-m3"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "job_knowledge_chunks"
    sqlite_path: str = "storage/app.db"
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.55
    evaluation_report_dir: str = "storage/evaluations"

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_base_url and self.llm_model and self.llm_api_key)

    @property
    def sqlite_file(self) -> Path:
        path = Path(self.sqlite_path)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def evaluation_report_directory(self) -> Path:
        path = Path(self.evaluation_report_dir)
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
