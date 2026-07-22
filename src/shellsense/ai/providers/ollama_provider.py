from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from shellsense.ai.providers.base import (
    AIProvider,
    AIResponse,
    ModelInfo,
    ProviderConfig,
    ProviderInfo,
    TokenUsage,
)
from shellsense.core.exceptions import AIProviderError
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config)
        self._base_url = (
            config.base_url if config and config.base_url else "http://localhost:11434"
        )

    def generate(self, prompt: str, system_prompt: str = "") -> AIResponse:
        body: dict[str, Any] = {
            "model": self._config.model or "llama3.2",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self._config.temperature,
                "top_p": self._config.top_p,
                "num_predict": self._config.max_tokens,
            },
        }
        if system_prompt:
            body["system"] = system_prompt

        try:
            import time

            start = time.time()
            req = Request(
                f"{self._base_url}/api/generate",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=self._config.timeout) as resp:
                data = json.loads(resp.read().decode())
            latency = (time.time() - start) * 1000
        except URLError as e:
            raise AIProviderError(f"Ollama connection failed: {e.reason}") from e
        except Exception as e:
            raise AIProviderError(f"Ollama request failed: {e}") from e

        usage = TokenUsage(
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            total_tokens=(data.get("prompt_eval_count", 0) + data.get("eval_count", 0)),
            latency_ms=latency,
        )
        return AIResponse(
            content=data.get("response", ""),
            model=data.get("model", self._config.model),
            provider="ollama",
            usage=usage,
            raw=data,
        )

    def generate_stream(
        self, prompt: str, system_prompt: str = ""
    ) -> AsyncIterator[str]:
        raise NotImplementedError("Async streaming requires asyncio")

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AIResponse:
        ollama_messages: list[dict[str, str]] = []
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        ollama_messages.extend(messages)

        body: dict[str, Any] = {
            "model": self._config.model or "llama3.2",
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": self._config.temperature,
                "top_p": self._config.top_p,
                "num_predict": self._config.max_tokens,
            },
        }

        try:
            import time

            start = time.time()
            req = Request(
                f"{self._base_url}/api/chat",
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=self._config.timeout) as resp:
                data = json.loads(resp.read().decode())
            latency = (time.time() - start) * 1000
        except URLError as e:
            raise AIProviderError(f"Ollama connection failed: {e.reason}") from e
        except Exception as e:
            raise AIProviderError(f"Ollama request failed: {e}") from e

        usage = TokenUsage(
            input_tokens=data.get("prompt_eval_count", 0)
            or data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            latency_ms=latency,
        )
        message = data.get("message", {})
        return AIResponse(
            content=message.get("content", ""),
            model=data.get("model", self._config.model),
            provider="ollama",
            usage=usage,
            raw=data,
        )

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        raise NotImplementedError("Async streaming requires asyncio")

    def get_models(self) -> list[ModelInfo]:
        try:
            req = Request(
                f"{self._base_url}/api/tags",
                method="GET",
            )
            with urlopen(req, timeout=self._config.timeout) as resp:
                data = json.loads(resp.read().decode())
            models: list[ModelInfo] = []
            for m in data.get("models", []):
                name = m.get("name", "")
                models.append(
                    ModelInfo(
                        id=name,
                        name=name,
                        provider="ollama",
                    )
                )
            return models
        except Exception as e:
            logger.warning("Failed to fetch Ollama models: %s", e)
            return [ModelInfo(id="llama3.2", name="Llama 3.2", provider="ollama")]

    def health_check(self) -> bool:
        try:
            req = Request(f"{self._base_url}/api/tags", method="GET")
            with urlopen(req, timeout=5) as resp:
                return bool(resp.status == 200)
        except Exception:
            return False

    def test_connection(self) -> bool:
        return self.health_check()

    @property
    def info(self) -> ProviderInfo:
        is_available = self.health_check()
        return ProviderInfo(
            name="ollama",
            display_name="Ollama",
            description="Local Ollama inference (fully offline)",
            version="1.0",
            website="https://ollama.ai",
            models=[],
            supports_streaming=True,
            requires_api_key=False,
            offline=True,
            available=is_available,
        )
