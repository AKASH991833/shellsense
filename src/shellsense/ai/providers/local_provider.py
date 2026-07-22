from __future__ import annotations

from collections.abc import AsyncIterator

from shellsense.ai.providers.base import (
    AIProvider,
    AIResponse,
    ModelInfo,
    ProviderConfig,
    ProviderInfo,
)
from shellsense.core.exceptions import AIProviderError
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class LocalProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config)

    def generate(self, prompt: str, system_prompt: str = "") -> AIResponse:
        raise AIProviderError(
            "Local LLM provider: architecture-ready stub. "
            "Configure a local model path or use Ollama for offline inference."
        )

    def generate_stream(
        self, prompt: str, system_prompt: str = ""
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AIResponse:
        raise AIProviderError("Local LLM provider not yet fully implemented")

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    def get_models(self) -> list[ModelInfo]:
        return [ModelInfo(id="local", name="Local LLM", provider="local")]

    def health_check(self) -> bool:
        return False

    def test_connection(self) -> bool:
        return False

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="local",
            display_name="Local LLM",
            description="Local LLM inference (architecture ready)",
            version="1.0",
            website="",
            models=[],
            supports_streaming=False,
            requires_api_key=False,
            offline=True,
            available=False,
        )
