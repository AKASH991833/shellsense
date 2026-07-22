from __future__ import annotations

import os

from shellsense.utils.config import ConfigManager
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

KEY_ENV_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def get_api_key(provider: str) -> str:
    env_var = KEY_ENV_MAP.get(provider, "")
    if env_var:
        key = os.environ.get(env_var, "")
        if key:
            return key

    config = ConfigManager()
    ai_config = config.get("ai", {})
    providers = ai_config.get("providers", {})
    pconfig = providers.get(provider, {})
    return str(pconfig.get("api_key", ""))


def set_api_key(provider: str, key: str) -> None:
    config = ConfigManager()
    ai_config = config.get("ai", {})
    if "providers" not in ai_config:
        ai_config["providers"] = {}
    if provider not in ai_config["providers"]:
        ai_config["providers"][provider] = {}
    ai_config["providers"][provider]["api_key"] = key
    config.set("ai", ai_config)
    logger.info("API key configured for provider: %s", provider)


def has_api_key(provider: str) -> bool:
    env_var = KEY_ENV_MAP.get(provider, "")
    if env_var and os.environ.get(env_var, ""):
        return True
    config = ConfigManager()
    ai_config = config.get("ai", {})
    providers = ai_config.get("providers", {})
    pconfig = providers.get(provider, {})
    key = pconfig.get("api_key", "")
    return bool(key)
