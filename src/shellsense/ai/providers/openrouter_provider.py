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


class OpenRouterProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config)
        self._base_url = "https://openrouter.ai/api/v1"

    def generate(self, prompt: str, system_prompt: str = "") -> AIResponse:
        raise AIProviderError(
            "OpenRouter provider: architecture-ready stub. "
            "Set OPENROUTER_API_KEY and install 'openai' package to use."
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
        raise AIProviderError("OpenRouter provider not yet fully implemented")

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    def get_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id="openai/gpt-4o-mini", name="GPT-4o Mini", provider="openrouter"
            ),
            ModelInfo(
                id="anthropic/claude-sonnet",
                name="Claude Sonnet",
                provider="openrouter",
            ),
        ]

    def health_check(self) -> bool:
        return bool(self._config.api_key)

    def test_connection(self) -> bool:
        return self.health_check()

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="openrouter",
            display_name="OpenRouter",
            description="OpenRouter multi-provider gateway (architecture ready)",
            version="1.0",
            website="https://openrouter.ai",
            models=[],
            supports_streaming=True,
            requires_api_key=True,
            offline=False,
            available=bool(self._config.api_key),
        )
