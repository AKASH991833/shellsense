from __future__ import annotations

from shellsense.knowledge.cache import SuggestionCache


class TestSuggestionCache:
    def test_set_and_get(self) -> None:
        cache = SuggestionCache(max_size=100, default_ttl=300.0)
        results = [{"name": "ls"}]
        cache.set("test_key", results)
        got = cache.get("test_key")
        assert got is not None
        assert len(got) == 1
        assert got[0]["name"] == "ls"

    def test_miss_returns_none(self) -> None:
        cache = SuggestionCache(max_size=100, default_ttl=300.0)
        got = cache.get("nonexistent")
        assert got is None

    def test_invalidate(self) -> None:
        cache = SuggestionCache(max_size=100, default_ttl=300.0)
        cache.set("key1", [{"name": "ls"}])
        cache.set("key2", [{"name": "cp"}])
        cache.invalidate("key1")
        assert cache.get("key1") is None
        assert cache.get("key2") is not None

    def test_clear(self) -> None:
        cache = SuggestionCache(max_size=100, default_ttl=300.0)
        cache.set("key1", [{"name": "ls"}])
        cache.set("key2", [{"name": "cp"}])
        cache.clear()
        assert cache.size == 0
        assert cache.get("key1") is None

    def test_eviction(self) -> None:
        cache = SuggestionCache(max_size=2, default_ttl=300.0)
        cache.set("a", [{"name": "ls"}])
        cache.set("b", [{"name": "cp"}])
        cache.set("c", [{"name": "mv"}])
        assert cache.size <= 2

    def test_expiry(self) -> None:
        cache = SuggestionCache(max_size=100, default_ttl=0)
        cache.set("key", [{"name": "ls"}])
        import time

        time.sleep(0.01)
        got = cache.get("key")
        assert got is None
