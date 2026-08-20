import httpx

from app.providers.base import ProviderResponseError, ProviderUnavailableError


class OllamaEmbeddingProvider:
    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.model_name = model
        self.client = client or httpx.Client(
            base_url=f"{base_url.rstrip('/')}/",
            timeout=timeout,
        )

    def ping(self) -> bool:
        try:
            response = self.client.get("api/tags")
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        return True

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self.client.post(
                "api/embed",
                json={"model": self.model_name, "input": texts},
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise ProviderUnavailableError("无法连接 Ollama Embedding 服务") from error

        embeddings = response.json().get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise ProviderResponseError("Ollama 返回的向量数量与输入数量不一致")
        if any(not isinstance(vector, list) or not vector for vector in embeddings):
            raise ProviderResponseError("Ollama 返回了无效向量")
        return embeddings
