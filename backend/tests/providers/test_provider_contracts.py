import json

import httpx
import pytest

from app.providers.base import ProviderResponseError
from app.providers.embedding.ollama import OllamaEmbeddingProvider
from app.providers.llm.openai_compatible import OpenAICompatibleLLMProvider


def test_ollama_embedding_provider_sends_batch_and_returns_vectors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/embed"
        assert json.loads(request.content) == {"model": "bge-m3", "input": ["岗位", "面试"]}
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama")
    provider = OllamaEmbeddingProvider("http://ollama", "bge-m3", client=client)

    assert provider.embed(["岗位", "面试"]) == [[0.1, 0.2], [0.3, 0.4]]


def test_ollama_embedding_provider_rejects_incomplete_batch() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})
    )
    client = httpx.Client(transport=transport, base_url="http://ollama")
    provider = OllamaEmbeddingProvider("http://ollama", "bge-m3", client=client)

    with pytest.raises(ProviderResponseError, match="数量"):
        provider.embed(["岗位", "面试"])


def test_openai_compatible_provider_returns_message_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-token"
        body = json.loads(request.content)
        assert body["model"] == "demo-model"
        assert body["messages"][0]["role"] == "user"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "带引用的答案"}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://llm/v1")
    provider = OpenAICompatibleLLMProvider(
        base_url="http://llm/v1",
        api_key="test-token",
        model="demo-model",
        client=client,
    )

    result = provider.complete([{"role": "user", "content": "问题"}])

    assert result == "带引用的答案"
