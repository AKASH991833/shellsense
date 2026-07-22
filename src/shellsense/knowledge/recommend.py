from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.cache import SuggestionCache
from shellsense.knowledge.search import (
    get_command_by_name,
    get_related_for_command,
    search_by_category,
)
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

_recommend_cache = SuggestionCache(max_size=200, default_ttl=600.0)


def recommend_for_command(
    db: DatabaseManager,
    command_name: str,
    limit: int = 10,
) -> list[dict[str, object]]:
    cache_key = f"recommend:{command_name}:{limit}"
    cached = _recommend_cache.get(cache_key)
    if cached is not None:
        return cached[:limit]

    cmd = get_command_by_name(db, command_name)
    if not cmd:
        return []

    cmd_id_raw = cmd.get("id")
    cmd_id = int(str(cmd_id_raw)) if cmd_id_raw is not None else None
    results: list[dict[str, object]] = []
    seen: set[str] = set()

    if cmd_id is not None:
        related_raw = get_related_for_command(db, cmd_id)
        for r in related_raw:
            rel_name = str(r.get("related_command_name", ""))
            rel_cmd = get_command_by_name(db, rel_name)
            if rel_cmd:
                rel_name_fixed = str(rel_cmd.get("name", rel_name))
                if rel_name_fixed not in seen:
                    seen.add(rel_name_fixed)
                    rel_cmd["relationship"] = r.get("relationship", "")
                    results.append(rel_cmd)

    category = str(cmd.get("category", ""))
    if category:
        same_cat = search_by_category(db, category, limit=20)
        for sc in same_cat:
            sc_name = str(sc.get("name", ""))
            if sc_name != command_name and sc_name not in seen:
                seen.add(sc_name)
                results.append(sc)

    _recommend_cache.set(cache_key, results)
    return results[:limit]


def find_similar_commands(
    db: DatabaseManager,
    command_name: str,
    limit: int = 10,
) -> list[dict[str, object]]:
    cache_key = f"similar:{command_name}:{limit}"
    cached = _recommend_cache.get(cache_key)
    if cached is not None:
        return cached[:limit]

    cmd = get_command_by_name(db, command_name)
    if not cmd:
        return []

    cmd_id_raw = cmd.get("id")
    cmd_id = int(str(cmd_id_raw)) if cmd_id_raw is not None else None
    category = str(cmd.get("category", ""))
    difficulty = str(cmd.get("difficulty", ""))
    keywords = str(cmd.get("keywords", ""))
    keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]

    results: list[dict[str, object]] = []
    seen: set[str] = set()

    if cmd_id is not None:
        related_raw = get_related_for_command(db, cmd_id)
        for r in related_raw:
            rel_name = str(r.get("related_command_name", ""))
            rel_cmd = get_command_by_name(db, rel_name)
            if rel_cmd:
                rel_name_fixed = str(rel_cmd.get("name", rel_name))
                if rel_name_fixed not in seen:
                    seen.add(rel_name_fixed)
                rel_cmd["similarity_reason"] = "related"
                results.append(rel_cmd)

    if category:
        same_cat = search_by_category(db, category, limit=30)
        for sc in same_cat:
            sc_name = str(sc.get("name", ""))
            if sc_name != command_name and sc_name not in seen:
                sc_difficulty = str(sc.get("difficulty", ""))
                reason = "same_category"
                if sc_difficulty == difficulty:
                    reason = "same_category_difficulty"
                sc["similarity_reason"] = reason
                seen.add(sc_name)
                results.append(sc)

    if keyword_list:
        from shellsense.knowledge.search import search_commands

        for kw in keyword_list:
            kw_results = search_commands(db, kw, limit=5)
            for kr in kw_results:
                kr_name = str(kr.get("name", ""))
                if kr_name != command_name and kr_name not in seen:
                    kr["similarity_reason"] = "keyword_match"
                    seen.add(kr_name)
                    results.append(kr)

    _recommend_cache.set(cache_key, results)
    return results[:limit]
