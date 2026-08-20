from app.core.config import Settings
from app.services.container import ServiceContainer


def test_container_builds_ollama_embedding_provider() -> None:
    container = ServiceContainer(
        Settings(
            embedding_base_url="http://ollama:11434",
            embedding_model="bge-m3",
        )
    )

    assert container.embeddings.model_name == "bge-m3"

