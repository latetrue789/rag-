from typing import Literal, Protocol, TypedDict


class ProviderError(RuntimeError):
    """Base model-provider error."""


class ProviderUnavailableError(ProviderError):
    """Raised when a configured provider cannot be reached."""


class ProviderResponseError(ProviderError):
    """Raised when a provider returns an invalid response."""


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class EmbeddingProvider(Protocol):
    model_name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LLMProvider(Protocol):
    model_name: str

    def complete(self, messages: list[ChatMessage]) -> str: ...
