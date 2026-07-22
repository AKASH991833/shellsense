from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from urllib.request import Request, urlopen

from shellsense.ai.providers.base import (
    AIProvider,
    AIResponse,
    ModelInfo,
    ProviderConfig,
    ProviderInfo,
    TokenUsage,
)
from shellsense.core.exceptions import (
    AIAuthenticationError,
    AIModelNotFoundError,
    AIProviderError,
    AIQuotaExceededError,
    AIRateLimitError,
)
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config)
        self._base_url = (
            config.base_url
            if config and config.base_url
            else "https://api.openai.com/v1"
        )

    def _headers(self) -> dict[str, str]:
        key = self._config.api_key
        if not key:
            raise AIAuthenticationError("OpenAI API key not configured")
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _handle_error(self, status: int, body: dict[str, Any]) -> None:
        if status == 401:
            raise AIAuthenticationError("Invalid OpenAI API key")
        elif status == 429:
            raise AIRateLimitError("OpenAI rate limit exceeded")
        elif status == 402:
            raise AIQuotaExceededError("OpenAI quota exceeded")
        elif status == 404:
            raise AIModelNotFoundError(f"OpenAI model not found: {self._config.model}")
        elif status >= 400:
            error_msg = body.get("error", {}).get("message", str(body))
            raise AIProviderError(f"OpenAI error ({status}): {error_msg}")

    def generate(self, prompt: str, system_prompt: str = "") -> AIResponse:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)

    def generate_stream(
        self, prompt: str, system_prompt: str = ""
    ) -> AsyncIterator[str]:
        raise NotImplementedError("Sync streaming not supported, use chat_stream")

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AIResponse:
        body: dict[str, Any] = {
            "model": self._config.model or "gpt-4o-mini",
            "messages": messages,
            "temperature": self._config.temperature,
            "top_p": self._config.top_p,
            "max_tokens": self._config.max_tokens,
        }
        req = Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(body).encode(),
            headers=self._headers(),
            method="POST",
        )
        try:
            import time

            start = time.time()
            with urlopen(req, timeout=self._config.timeout) as resp:
                data = json.loads(resp.read().decode())
            latency = (time.time() - start) * 1000
        except AIAuthenticationError:
            raise
        except AIRateLimitError:
            raise
        except AIQuotaExceededError:
            raise
        except Exception as e:
            raise AIProviderError(f"OpenAI request failed: {e}") from e

        choice = data["choices"][0]
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            latency_ms=latency,
        )
        return AIResponse(
            content=choice["message"]["content"],
            model=data["model"],
            provider="openai",
            usage=usage,
            raw=data,
        )

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        raise NotImplementedError("Async streaming requires asyncio event loop")

    def get_models(self) -> list[ModelInfo]:
        try:
            req = Request(
                f"{self._base_url}/models",
                headers=self._headers(),
                method="GET",
            )
            with urlopen(req, timeout=self._config.timeout) as resp:
                data = json.loads(resp.read().decode())
            models: list[ModelInfo] = []
            for m in data.get("data", []):
                models.append(
                    ModelInfo(
                        id=m["id"],
                        name=m["id"],
                        provider="openai",
                    )
                )
            return models
        except Exception as e:
            logger.warning("Failed to fetch OpenAI models: %s", e)
            return [
                ModelInfo(id="gpt-4o-mini", name="GPT-4o Mini", provider="openai"),
                ModelInfo(id="gpt-4o", name="GPT-4o", provider="openai"),
            ]

    def health_check(self) -> bool:
        try:
            req = Request(
                f"{self._base_url}/models",
                headers=self._headers(),
                method="GET",
            )
            with urlopen(req, timeout=10) as resp:
                return bool(resp.status == 200)
        except Exception:
            return False

    def test_connection(self) -> bool:
        return self.health_check()

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="openai",
            display_name="OpenAI",
            description="OpenAI GPT models (requires API key)",
            version="1.0",
            website="https://openai.com",
            models=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            supports_streaming=True,
            requires_api_key=True,
            offline=False,
            available=bool(self._config.api_key),
        )
