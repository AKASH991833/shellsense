from __future__ import annotations

import time
from threading import Lock

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

CacheEntry = dict[str, object]
CacheData = dict[str, CacheEntry]


class SuggestionCache:
    def __init__(self, max_size: int = 500, default_ttl: float = 300.0) -> None:
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._data: CacheData = {}
        self._expiry: dict[str, float] = {}
        self._lock = Lock()

    def get(self, key: str) -> list[dict[str, object]] | None:
        with self._lock:
            if key not in self._data:
                return None
            if time.time() > self._expiry.get(key, 0):
                del self._data[key]
                del self._expiry[key]
                logger.debug("Cache expired: %s", key)
                return None
            logger.debug("Cache hit: %s", key)
            return self._data[key].get("results")  # type: ignore[return-value]

    def set(
        self,
        key: str,
        results: list[dict[str, object]],
        ttl: float | None = None,
    ) -> None:
        with self._lock:
            if len(self._data) >= self._max_size:
                self._evict_one()
            self._data[key] = {"results": results}
            self._expiry[key] = time.time() + (ttl or self._default_ttl)
            logger.debug("Cache set: %s (%d results)", key, len(results))

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self._expiry.clear()
            logger.debug("Cache cleared")

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._data)

    def _evict_one(self) -> None:
        if not self._data:
            return
        oldest = min(self._expiry, key=lambda k: self._expiry[k])
        del self._data[oldest]
        del self._expiry[oldest]
        logger.debug("Evicted cache entry: %s", oldest)
