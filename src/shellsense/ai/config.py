from __future__ import annotations

from typing import Any

from shellsense.utils.config import ConfigManager
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


PROVIDER_NAMES = ["openai", "gemini", "ollama", "claude", "openrouter", "local"]

DEFAULT_AI_CONFIG: dict[str, Any] = {
    "default_provider": "ollama",
    "providers": {
        "openai": {
            "api_key": "",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 1024,
            "timeout": 30,
        },
        "gemini": {
            "api_key": "",
            "model": "gemini-2.0-flash",
            "temperature": 0.3,
            "max_tokens": 1024,
            "timeout": 30,
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama3.2",
            "temperature": 0.3,
            "max_tokens": 1024,
            "timeout": 60,
        },
        "claude": {
            "api_key": "",
            "model": "claude-sonnet-4-20250514",
            "temperature": 0.3,
            "max_tokens": 1024,
            "timeout": 30,
        },
        "openrouter": {
            "api_key": "",
            "model": "openai/gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 1024,
            "timeout": 30,
        },
        "local": {
            "model_path": "",
            "model": "local",
            "temperature": 0.3,
            "max_tokens": 1024,
        },
    },
    "features": {
        "streaming": True,
        "conversation_history": True,
        "response_cache": True,
        "token_tracking": True,
    },
}


def get_ai_config() -> dict[str, Any]:
    config = ConfigManager()
    ai_config = config.get("ai", {})
    merged = dict(DEFAULT_AI_CONFIG)
    merged.update(ai_config)
    return merged


def get_provider_config(provider: str) -> dict[str, Any]:
    ai_config = get_ai_config()
    providers: dict[str, Any] = ai_config.get("providers", {})
    result: dict[str, Any] = providers.get(provider, {})
    return result


def get_default_provider() -> str:
    ai_config = get_ai_config()
    default: str = ai_config.get("default_provider", "ollama")
    return default


def set_default_provider(provider: str) -> None:
    if provider not in PROVIDER_NAMES:
        raise ValueError(
            f"Unknown provider: {provider}. Choose from: {', '.join(PROVIDER_NAMES)}"
        )
    config = ConfigManager()
    ai_config = config.get("ai", {})
    ai_config["default_provider"] = provider
    config.set("ai", ai_config)
    logger.info("Default AI provider set to: %s", provider)


def get_available_providers() -> list[str]:
    return list(PROVIDER_NAMES)
