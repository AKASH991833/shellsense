from __future__ import annotations

from collections.abc import AsyncIterator

from shellsense.ai.providers.base import (
    AIProvider,
    AIResponse,
    ModelInfo,
    ProviderConfig,
    ProviderInfo,
)
from shellsense.core.exceptions import AIAuthenticationError, AIProviderError
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class ClaudeProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config)
        self._base_url = "https://api.anthropic.com/v1"

    def _get_api_key(self) -> str:
        key = self._config.api_key
        if not key:
            raise AIAuthenticationError("Claude API key not configured")
        return key

    def generate(self, prompt: str, system_prompt: str = "") -> AIResponse:
        raise AIProviderError(
            "Claude provider: install 'anthropic' package to use this provider. "
            "This is an architecture-ready stub."
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
        raise AIProviderError(
            "Claude provider: install 'anthropic' package to use this provider. "
            "This is an architecture-ready stub."
        )

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    def get_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id="claude-sonnet-4-20250514", name="Claude Sonnet 4", provider="claude"
            ),
            ModelInfo(
                id="claude-haiku-3-5-20241022",
                name="Claude Haiku 3.5",
                provider="claude",
            ),
        ]

    def health_check(self) -> bool:
        return bool(self._config.api_key)

    def test_connection(self) -> bool:
        return self.health_check()

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="claude",
            display_name="Anthropic Claude",
            description="Anthropic Claude models (architecture ready, requires anthropic package)",
            version="1.0",
            website="https://anthropic.com",
            models=["claude-sonnet-4-20250514", "claude-haiku-3-5-20241022"],
            supports_streaming=True,
            requires_api_key=True,
            offline=False,
            available=bool(self._config.api_key),
        )
