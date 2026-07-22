from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderConfig:
    api_key: str = ""
    model: str = ""
    temperature: float = 0.3
    top_p: float = 1.0
    max_tokens: int = 1024
    timeout: float = 30.0
    retries: int = 3
    base_url: str = ""
    organization: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderInfo:
    name: str = ""
    display_name: str = ""
    description: str = ""
    version: str = ""
    website: str = ""
    models: list[str] = field(default_factory=list)
    supports_streaming: bool = True
    supports_embeddings: bool = False
    supports_conversation: bool = True
    requires_api_key: bool = True
    offline: bool = False
    available: bool = False


@dataclass
class ModelInfo:
    id: str = ""
    name: str = ""
    provider: str = ""
    context_length: int = 4096
    pricing_input: float = 0.0
    pricing_output: float = 0.0
    supports_streaming: bool = True
    supports_functions: bool = False


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: float = 0.0


@dataclass
class AIResponse:
    content: str = ""
    model: str = ""
    provider: str = ""
    usage: TokenUsage = field(default_factory=TokenUsage)
    raw: dict[str, Any] = field(default_factory=dict)
    finished: bool = True


class AIProvider(ABC):
    def __init__(self, config: ProviderConfig | None = None) -> None:
        self._config = config or ProviderConfig()

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> AIResponse: ...

    @abstractmethod
    def generate_stream(
        self, prompt: str, system_prompt: str = ""
    ) -> AsyncIterator[str]: ...

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AIResponse: ...

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AsyncIterator[str]: ...

    @abstractmethod
    def get_models(self) -> list[ModelInfo]: ...

    @abstractmethod
    def health_check(self) -> bool: ...

    @abstractmethod
    def test_connection(self) -> bool: ...

    @property
    @abstractmethod
    def info(self) -> ProviderInfo: ...

    def count_tokens(self, text: str) -> int:
        return len(text.split())
