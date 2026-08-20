import httpx

from app.providers.base import (
    ChatMessage,
    ProviderResponseError,
    ProviderUnavailableError,
)


class OpenAICompatibleLLMProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        timeout: float = 60.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.model_name = model
        self.api_key = api_key
        self.client = client or httpx.Client(
            base_url=f"{base_url.rstrip('/')}/",
            timeout=timeout,
        )

    def complete(self, messages: list[ChatMessage]) -> str:
        try:
            response = self.client.post(
                "chat/completions",
                json={"model": self.model_name, "messages": messages},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise ProviderUnavailableError("无法连接在线 LLM 服务") from error

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ProviderResponseError("LLM 返回格式无效") from error
        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseError("LLM 返回了空答案")
        return content.strip()
