from __future__ import annotations

import hashlib
import json
import time
from threading import Lock

from shellsense.ai.providers.base import AIResponse
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_shellsense_dir

logger = get_logger(__name__)


class AICache:
    def __init__(
        self, max_memory: int = 200, ttl: float = 600.0, use_disk: bool = True
    ) -> None:
        self._max_memory = max_memory
        self._ttl = ttl
        self._memory: dict[str, AIResponse] = {}
        self._expiry: dict[str, float] = {}
        self._lock = Lock()
        self._use_disk = use_disk
        if use_disk:
            self._disk_dir = get_shellsense_dir() / "ai_cache"
            self._disk_dir.mkdir(parents=True, exist_ok=True)

    def _make_key(self, prompt: str, system_prompt: str = "", model: str = "") -> str:
        raw = f"{prompt}||{system_prompt}||{model}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(
        self, prompt: str, system_prompt: str = "", model: str = ""
    ) -> AIResponse | None:
        key = self._make_key(prompt, system_prompt, model)
        with self._lock:
            if key in self._memory:
                if time.time() < self._expiry.get(key, 0):
                    logger.debug("AI cache hit (memory): %s...", prompt[:40])
                    return self._memory[key]
                else:
                    self._memory.pop(key, None)
                    self._expiry.pop(key, None)

        if self._use_disk:
            cached = self._read_disk(key)
            if cached is not None:
                with self._lock:
                    if len(self._memory) < self._max_memory:
                        self._memory[key] = cached
                        self._expiry[key] = time.time() + self._ttl
                return cached

        return None

    def set(
        self,
        prompt: str,
        response: AIResponse,
        system_prompt: str = "",
        model: str = "",
        ttl: float | None = None,
    ) -> None:
        key = self._make_key(prompt, system_prompt, model)
        expires = time.time() + (ttl or self._ttl)

        with self._lock:
            if len(self._memory) >= self._max_memory:
                oldest = min(self._expiry, key=lambda k: self._expiry[k])
                self._memory.pop(oldest, None)
                self._expiry.pop(oldest, None)
            self._memory[key] = response
            self._expiry[key] = expires

        if self._use_disk:
            self._write_disk(key, response, expires)

    def invalidate(self, prompt: str, system_prompt: str = "", model: str = "") -> None:
        key = self._make_key(prompt, system_prompt, model)
        with self._lock:
            self._memory.pop(key, None)
            self._expiry.pop(key, None)
        if self._use_disk:
            path = self._disk_dir / f"{key}.json"
            if path.exists():
                path.unlink()

    def clear(self) -> None:
        with self._lock:
            self._memory.clear()
            self._expiry.clear()
        if self._use_disk:
            for path in self._disk_dir.glob("*.json"):
                path.unlink()
        logger.info("AI cache cleared")

    def _read_disk(self, key: str) -> AIResponse | None:
        path = self._disk_dir / f"{key}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            expires = data.get("_expires", 0)
            if time.time() > expires:
                path.unlink()
                return None
            usage_data = data.get("usage", {})
            from shellsense.ai.providers.base import TokenUsage

            usage = TokenUsage(
                input_tokens=usage_data.get("input_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                estimated_cost=usage_data.get("estimated_cost", 0.0),
                latency_ms=usage_data.get("latency_ms", 0.0),
            )
            return AIResponse(
                content=data.get("content", ""),
                model=data.get("model", ""),
                provider=data.get("provider", ""),
                usage=usage,
                raw=data.get("raw", {}),
            )
        except Exception as e:
            logger.debug("Failed to read cache: %s", e)
            return None

    def _write_disk(self, key: str, response: AIResponse, expires: float) -> None:
        path = self._disk_dir / f"{key}.json"
        try:
            data = {
                "_expires": expires,
                "content": response.content,
                "model": response.model,
                "provider": response.provider,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "estimated_cost": response.usage.estimated_cost,
                    "latency_ms": response.usage.latency_ms,
                },
                "raw": response.raw,
            }
            path.write_text(json.dumps(data))
        except Exception as e:
            logger.debug("Failed to write cache: %s", e)
