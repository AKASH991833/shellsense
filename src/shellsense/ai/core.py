from __future__ import annotations

from threading import Lock
from typing import Any

from shellsense.ai.cache import AICache
from shellsense.ai.config import (
    get_ai_config,
    get_provider_config,
)
from shellsense.ai.context import AIContext
from shellsense.ai.memory import AIMemory
from shellsense.ai.prompts import PromptEngine
from shellsense.ai.providers.base import (
    AIProvider,
    AIResponse,
    ModelInfo,
    ProviderConfig,
    ProviderInfo,
)
from shellsense.ai.security import get_api_key, has_api_key
from shellsense.ai.session import SessionManager
from shellsense.ai.tokenizer import TokenTracker, UsageRecord
from shellsense.core.exceptions import AIConfigurationError, AIProviderError
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class AIEngine:
    def __init__(self) -> None:
        self._provider: AIProvider | None = None
        self._provider_name: str = ""
        self._lock = Lock()
        self._initialized = False

        self.prompts = PromptEngine()
        self.context = AIContext()
        self.memory = AIMemory()
        self.sessions = SessionManager()
        self.tokens = TokenTracker()
        self.cache = AICache()
        self._load_config()

    def _load_config(self) -> None:
        ai_config = get_ai_config()
        self._provider_name = ai_config.get("default_provider", "ollama")
        features = ai_config.get("features", {})
        if not features.get("response_cache", True):
            self.cache.clear()
        if not features.get("token_tracking", True):
            self.tokens = TokenTracker()

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def _get_provider_instance(self, provider: str) -> AIProvider:
        from shellsense.ai.providers.claude_provider import ClaudeProvider
        from shellsense.ai.providers.gemini_provider import GeminiProvider
        from shellsense.ai.providers.local_provider import LocalProvider
        from shellsense.ai.providers.ollama_provider import OllamaProvider
        from shellsense.ai.providers.openai_provider import OpenAIProvider
        from shellsense.ai.providers.openrouter_provider import OpenRouterProvider

        providers: dict[str, type[AIProvider]] = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
            "ollama": OllamaProvider,
            "claude": ClaudeProvider,
            "openrouter": OpenRouterProvider,
            "local": LocalProvider,
        }

        provider_cls = providers.get(provider)
        if provider_cls is None:
            raise AIConfigurationError(f"Unknown provider: {provider}")

        config_data = get_provider_config(provider)
        api_key = get_api_key(provider)

        pconfig = ProviderConfig(
            api_key=api_key,
            model=str(config_data.get("model", "")),
            temperature=float(config_data.get("temperature", 0.3)),
            max_tokens=int(config_data.get("max_tokens", 1024)),
            timeout=float(config_data.get("timeout", 30.0)),
            base_url=str(config_data.get("base_url", "")),
        )
        return provider_cls(pconfig)

    def _ensure_provider(self, provider: str | None = None) -> AIProvider:
        name = provider or self._provider_name
        if self._provider is None or self._provider_name != name:
            with self._lock:
                self._provider = self._get_provider_instance(name)
                self._provider_name = name
                self._initialized = True
        return self._provider

    def set_provider(self, provider: str) -> None:
        if provider not in (
            "openai",
            "gemini",
            "ollama",
            "claude",
            "openrouter",
            "local",
        ):
            raise AIConfigurationError(f"Unknown provider: {provider}")
        with self._lock:
            self._provider_name = provider
            self._provider = None
        logger.info("AI provider set to: %s", provider)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        provider: str | None = None,
        use_cache: bool = True,
    ) -> AIResponse:
        p = self._ensure_provider(provider)
        model = p.config.model

        if use_cache:
            cached = self.cache.get(prompt, system_prompt, model)
            if cached is not None:
                return cached

        if not system_prompt:
            system_prompt = self.prompts.get_system_prompt()

        try:
            import time

            start = time.time()
            response = p.generate(prompt, system_prompt)
            latency = (time.time() - start) * 1000

            response.usage.latency_ms = latency
            response.usage.estimated_cost = self.tokens.estimate_cost(
                self._provider_name,
                response.usage.input_tokens,
                response.usage.output_tokens,
            )

            self.tokens.record_usage(
                UsageRecord(
                    provider=self._provider_name,
                    model=response.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.total_tokens,
                    cost=response.usage.estimated_cost,
                    latency_ms=latency,
                    timestamp="",
                )
            )

            self.memory.add_to_history(
                {
                    "provider": self._provider_name,
                    "model": response.model,
                    "prompt": prompt[:200],
                    "response": response.content[:200],
                    "tokens": response.usage.total_tokens,
                }
            )

            if use_cache:
                self.cache.set(prompt, response, system_prompt, model)

            return response
        except Exception as e:
            logger.error("AI generate failed: %s", e)
            raise AIProviderError(str(e)) from e

    def chat(
        self,
        message: str,
        session_id: str | None = None,
        provider: str | None = None,
        system_prompt: str = "",
    ) -> AIResponse:
        p = self._ensure_provider(provider)

        if session_id:
            conv = self.sessions.get_session(session_id)
            if conv is None:
                conv = self.sessions.create_session(
                    provider=self._provider_name,
                    model=p.config.model,
                    system_prompt=system_prompt or self.prompts.get_system_prompt(),
                )
        else:
            conv = self.sessions.get_active_session()
            if conv is None:
                conv = self.sessions.create_session(
                    provider=self._provider_name,
                    model=p.config.model,
                    system_prompt=system_prompt or self.prompts.get_system_prompt(),
                )

        conv.add_message("user", message)
        msgs = list(conv.messages)
        sp = conv.system_prompt or system_prompt or self.prompts.get_system_prompt()

        try:
            import time

            start = time.time()
            response = p.chat(msgs, sp)
            latency = (time.time() - start) * 1000

            response.usage.latency_ms = latency
            response.usage.estimated_cost = self.tokens.estimate_cost(
                self._provider_name,
                response.usage.input_tokens,
                response.usage.output_tokens,
            )

            conv.add_message("assistant", response.content)
            self.sessions.save_session()

            self.tokens.record_usage(
                UsageRecord(
                    provider=self._provider_name,
                    model=response.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.total_tokens,
                    cost=response.usage.estimated_cost,
                    latency_ms=latency,
                    timestamp="",
                )
            )

            return response
        except Exception as e:
            logger.error("AI chat failed: %s", e)
            raise AIProviderError(str(e)) from e

    def get_models(self, provider: str | None = None) -> list[ModelInfo]:
        p = self._ensure_provider(provider)
        return p.get_models()

    def health_check(self, provider: str | None = None) -> bool:
        try:
            p = self._ensure_provider(provider)
            return p.health_check()
        except Exception:
            return False

    def test_connection(self, provider: str | None = None) -> bool:
        return self.health_check(provider)

    def get_provider_info(self, provider: str | None = None) -> ProviderInfo:
        p = self._ensure_provider(provider)
        return p.info

    def list_providers(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for name in ("openai", "gemini", "ollama", "claude", "openrouter", "local"):
            try:
                p = self._get_provider_instance(name)
                info = p.info
                result.append(
                    {
                        "name": info.name,
                        "display_name": info.display_name,
                        "description": info.description,
                        "available": info.available,
                        "offline": info.offline,
                        "requires_api_key": info.requires_api_key,
                        "has_api_key": has_api_key(name),
                    }
                )
            except Exception as e:
                result.append(
                    {
                        "name": name,
                        "display_name": name.title(),
                        "description": str(e),
                        "available": False,
                        "offline": False,
                        "requires_api_key": True,
                        "has_api_key": False,
                    }
                )
        return result

    @property
    def is_ready(self) -> bool:
        try:
            p = self._ensure_provider()
            info = p.info
            if info.requires_api_key and not has_api_key(self._provider_name):
                return False
            return True
        except Exception:
            return False
