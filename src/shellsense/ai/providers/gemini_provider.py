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
    AIProviderError,
    AIQuotaExceededError,
    AIRateLimitError,
)
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(AIProvider):
    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config)
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def _api_key(self) -> str:
        key = self._config.api_key
        if not key:
            raise AIAuthenticationError("Gemini API key not configured")
        return key

    def _handle_error(self, status: int, body: dict[str, Any]) -> None:
        error = body.get("error", {})
        if status == 403:
            raise AIAuthenticationError("Invalid Gemini API key")
        elif status == 429:
            raise AIRateLimitError("Gemini rate limit exceeded")
        elif status == 402:
            raise AIQuotaExceededError("Gemini quota exceeded")
        elif status >= 400:
            msg = error.get("message", str(body))
            raise AIProviderError(f"Gemini error ({status}): {msg}")

    def generate(self, prompt: str, system_prompt: str = "") -> AIResponse:
        body: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self._config.temperature,
                "topP": self._config.top_p,
                "maxOutputTokens": self._config.max_tokens,
            },
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        model = self._config.model or "gemini-2.0-flash"
        url = f"{self._base_url}/models/{model}:generateContent?key={self._api_key}"
        req = Request(url, data=json.dumps(body).encode(), method="POST")
        req.add_header("Content-Type", "application/json")

        try:
            import time

            start = time.time()
            with urlopen(req, timeout=self._config.timeout) as resp:
                data = json.loads(resp.read().decode())
            latency = (time.time() - start) * 1000
        except Exception as e:
            raise AIProviderError(f"Gemini request failed: {e}") from e

        candidates = data.get("candidates", [])
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)

        usage_data = data.get("usageMetadata", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("promptTokenCount", 0),
            output_tokens=usage_data.get("candidatesTokenCount", 0),
            total_tokens=usage_data.get("totalTokenCount", 0),
            latency_ms=latency,
        )
        return AIResponse(
            content=content,
            model=model,
            provider="gemini",
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
        contents: list[dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": text}]})
        if not contents:
            contents = [{"parts": [{"text": ""}]}]
        prompt = contents[-1]["parts"][0]["text"] if contents else ""
        return self.generate(prompt, system_prompt)

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        raise NotImplementedError("Async streaming requires asyncio")

    def get_models(self) -> list[ModelInfo]:
        try:
            url = f"{self._base_url}/models?key={self._api_key}"
            req = Request(url, method="GET")
            with urlopen(req, timeout=self._config.timeout) as resp:
                data = json.loads(resp.read().decode())
            models: list[ModelInfo] = []
            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                if "gemini" in name:
                    models.append(ModelInfo(id=name, name=name, provider="gemini"))
            return models
        except Exception as e:
            logger.warning("Failed to fetch Gemini models: %s", e)
            return [
                ModelInfo(
                    id="gemini-2.0-flash", name="Gemini 2.0 Flash", provider="gemini"
                ),
                ModelInfo(
                    id="gemini-2.0-pro", name="Gemini 2.0 Pro", provider="gemini"
                ),
            ]

    def health_check(self) -> bool:
        try:
            url = f"{self._base_url}/models?key={self._api_key}"
            req = Request(url, method="GET")
            with urlopen(req, timeout=10) as resp:
                return bool(resp.status == 200)
        except Exception:
            return False

    def test_connection(self) -> bool:
        return self.health_check()

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="gemini",
            display_name="Google Gemini",
            description="Google Gemini models (requires API key)",
            version="1.0",
            website="https://ai.google.dev",
            models=["gemini-2.0-flash", "gemini-2.0-pro"],
            supports_streaming=True,
            requires_api_key=True,
            offline=False,
            available=bool(self._config.api_key),
        )
