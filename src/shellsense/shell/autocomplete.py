from __future__ import annotations

import time

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.cache import SuggestionCache
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

_ac_cache = SuggestionCache(max_size=200, default_ttl=60.0)

SUGGESTION_DELAY = 0.05


def get_autocomplete_suggestions(
    partial: str,
    limit: int = 10,
    max_time_ms: int = 50,
) -> list[dict[str, object]]:
    if not partial or not partial.strip():
        return []

    partial = partial.strip()
    cache_key = f"ac:{partial}:{limit}"
    cached = _ac_cache.get(cache_key)
    if cached is not None:
        return cached[:limit]

    start = time.time()

    db = DatabaseManager()
    engine = KnowledgeEngine(db)

    if " " in partial:
        results = engine.predict(partial, limit=limit)
    else:
        results = engine.suggest(partial, limit=limit)

    elapsed = time.time() - start
    if elapsed > max_time_ms / 1000.0:
        logger.debug("Autocomplete slow: %.2fms for '%s'", elapsed * 1000, partial)

    _ac_cache.set(cache_key, results)
    db.close()
    return results[:limit]
