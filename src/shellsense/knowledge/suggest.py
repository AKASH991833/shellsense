from __future__ import annotations

import threading
from typing import Any

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.cache import SuggestionCache
from shellsense.knowledge.context import ContextEngine
from shellsense.knowledge.dataset import get_command_names as get_all_command_names
from shellsense.knowledge.history import (
    get_history_frequency_for,
    get_popularity_for,
    record_search,
)
from shellsense.knowledge.ranking import rank_suggestions
from shellsense.utils.logging import get_logger

try:
    from rapidfuzz import fuzz, process

    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

logger = get_logger(__name__)

_suggestion_cache = SuggestionCache(max_size=500, default_ttl=300.0)

_suggest_lock = threading.Lock()
_is_suggesting = False


def _get_workflow_suggestions(
    query: str,
    limit: int = 3,
) -> list[dict[str, object]]:
    try:
        from shellsense.context.inferrer import ShellStateInferrer
        from shellsense.workflows.matcher import WorkflowMatcher

        inferrer = ShellStateInferrer()
        state = inferrer.infer()
        matcher = WorkflowMatcher()
        wf_suggestions = matcher.get_suggestions(query, state=state, limit=limit)
        results: list[dict[str, object]] = []
        for ws in wf_suggestions:
            results.append(
                {
                    "name": ws.suggested_command,
                    "short_description": f"[workflow] {ws.description} (step {ws.step_number}/{ws.total_steps})",
                    "category": ws.category,
                    "_match_type": "workflow",
                    "_workflow_name": ws.workflow_name,
                    "_step": ws.step_number,
                    "_total_steps": ws.total_steps,
                }
            )
        return results
    except Exception:
        return []


def _direct_query(
    db: DatabaseManager,
    query: str,
    limit: int = 10,
) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE name LIKE ? LIMIT ?",
        (f"{query}%", limit),
    )
    return [dict(row) for row in cursor.fetchall()]


def suggest_commands(
    db: DatabaseManager,
    query: str,
    limit: int = 10,
    weights: dict[str, float] | None = None,
    context: ContextEngine | None = None,
) -> list[dict[str, object]]:
    global _is_suggesting
    with _suggest_lock:
        if _is_suggesting:
            return _direct_query(db, query, limit)
        _is_suggesting = True
    try:
        if not query or not query.strip():
            return _get_all_suggestions(db, limit=limit)

        query = query.strip()
        cache_key = f"suggest:{query}:{limit}"
        cached = _suggestion_cache.get(cache_key)
        if cached is not None:
            return cached[:limit]

        if " " in query:
            results = _predict_multi_word(db, query, limit=limit)
        else:
            results = _suggest_single_word(db, query, limit, weights, context)

        wf = _get_workflow_suggestions(query, limit=3)
        if wf:
            results = wf + results

        record_search(db, query, len(results))
        _suggestion_cache.set(cache_key, results)
        return results[:limit]
    finally:
        with _suggest_lock:
            _is_suggesting = False


def predict_commands(
    db: DatabaseManager,
    partial: str,
    limit: int = 10,
) -> list[dict[str, object]]:
    if not partial or not partial.strip():
        return []

    partial = partial.strip()
    cache_key = f"predict:{partial}:{limit}"
    cached = _suggestion_cache.get(cache_key)
    if cached is not None:
        return cached[:limit]

    if " " in partial:
        results = _predict_multi_word(db, partial, limit=limit)
    else:
        results = suggest_commands(db, partial, limit=limit)

    wf = _get_workflow_suggestions(partial, limit=3)
    if wf:
        results = wf + results

    _suggestion_cache.set(cache_key, results)
    return results[:limit]


def _get_all_suggestions(
    db: DatabaseManager, limit: int = 10
) -> list[dict[str, object]]:
    from shellsense.knowledge.search import list_all

    return list_all(db, limit=limit)


def _get_recency_score(db: DatabaseManager, command_name: str) -> float:
    cursor = db.execute(
        "SELECT last_used FROM usage_stats WHERE command_name = ?",
        (command_name,),
    )
    row = cursor.fetchone()
    if row and row["last_used"]:
        return 1.0
    return 0.0


def _suggest_single_word(
    db: DatabaseManager,
    query: str,
    limit: int = 10,
    weights: dict[str, float] | None = None,
    context: ContextEngine | None = None,
) -> list[dict[str, object]]:
    seen: set[int] = set()
    results: list[dict[str, object]] = []

    def _add(candidates: list[dict[str, Any]]) -> None:
        for c in candidates:
            cid = c.get("id")
            if isinstance(cid, int) and cid not in seen:
                seen.add(cid)
                name = str(c.get("name", ""))
                c["_history_freq"] = get_history_frequency_for(db, name)
                c["_recency_boost"] = _get_recency_score(db, name)
                context_category = context.session_category if context else ""
                if context_category and c.get("category") == context_category:
                    c["_category_bonus"] = True
                results.append(c)

    exact = _exact_name_search(db, query)
    _add(exact)

    prefix = _prefix_name_search(db, query)
    _add(prefix)

    if len(results) < limit:
        alias = _alias_name_search(db, query)
        _add(alias)

    if len(results) < limit:
        contains = _contains_name_search(db, query)
        _add(contains)

    if len(results) < limit:
        keyword = _keyword_name_search(db, query)
        _add(keyword)

    if len(results) < limit:
        fuzzy = _fuzzy_name_search(db, query)
        _add(fuzzy)

    discovered = _suggest_discovered(db, query)
    _add(discovered)

    for r in results:
        r["_popularity"] = get_popularity_for(db, str(r.get("name", "")))

    ranked = rank_suggestions(query, results, weights=weights)
    return ranked[:limit]


def _predict_multi_word(
    db: DatabaseManager,
    query: str,
    limit: int = 10,
) -> list[dict[str, object]]:
    parts = query.strip().split()
    if not parts:
        return []

    command_part = parts[0]
    sub_part = " ".join(parts[1:]) if len(parts) > 1 else ""

    from shellsense.knowledge.search import get_command_by_name

    cmd = get_command_by_name(db, command_part)
    if not cmd:
        if HAS_RAPIDFUZZ:
            names = get_all_command_names()
            raw = process.extract(
                command_part, names, scorer=fuzz.WRatio, score_cutoff=60, limit=5
            )
            fuzzy_matches = [(name, int(score)) for name, score, _ in raw]
        else:
            from shellsense.knowledge.fuzzy import spell_correct

            fuzzy_matches = spell_correct(command_part)
        if fuzzy_matches:
            cmd = get_command_by_name(db, fuzzy_matches[0][0])
    if not cmd:
        prefix_results = _prefix_name_search(db, command_part)
        if prefix_results:
            cmd = prefix_results[0]
        else:
            return []

    if not sub_part:
        cmd_copy = dict(cmd)
        cmd_copy["_match_type"] = "exact"
        cmd_copy["_popularity"] = get_popularity_for(db, command_part)
        cmd_copy["_history_freq"] = get_history_frequency_for(db, command_part)
        return [cmd_copy]

    sub_lower = sub_part.lower()
    cmd_id_raw = cmd.get("id")
    cmd_id = int(str(cmd_id_raw)) if cmd_id_raw is not None else None
    subcommands = _get_subcommands_for(db, cmd_id) if cmd_id is not None else []
    options = _get_options_for(db, cmd_id) if cmd_id is not None else []

    predictions: list[dict[str, object]] = []

    for sc in subcommands:
        sc_name = str(sc.get("subcommand", ""))
        if sc_name.lower().startswith(sub_lower):
            full = f"{command_part} {sc_name}"
            pred: dict[str, object] = {
                "name": full,
                "short_description": str(sc.get("description", "")),
                "category": cmd.get("category", ""),
                "difficulty": cmd.get("difficulty", ""),
                "risk_level": cmd.get("risk_level", ""),
                "_match_type": "prefix",
                "_popularity": 0,
                "_history_freq": 0,
            }
            predictions.append(pred)

    for opt in options:
        flag = str(opt.get("flag", ""))
        if flag.lower().startswith(sub_lower):
            full = f"{command_part} {flag}"
            pred = {
                "name": full,
                "short_description": str(opt.get("description", "")),
                "category": cmd.get("category", ""),
                "difficulty": cmd.get("difficulty", ""),
                "risk_level": cmd.get("risk_level", ""),
                "_match_type": "prefix",
                "_popularity": 0,
                "_history_freq": 0,
            }
            predictions.append(pred)

    if not predictions:
        for sc in subcommands:
            sc_name = str(sc.get("subcommand", ""))
            if sub_lower in sc_name.lower():
                full = f"{command_part} {sc_name}"
                pred = {
                    "name": full,
                    "short_description": str(sc.get("description", "")),
                    "category": cmd.get("category", ""),
                    "difficulty": cmd.get("difficulty", ""),
                    "risk_level": cmd.get("risk_level", ""),
                    "_match_type": "contains",
                    "_popularity": 0,
                    "_history_freq": 0,
                }
                predictions.append(pred)

    if not predictions:
        return []

    return predictions[:limit]


def _get_subcommands_for(db: DatabaseManager, cmd_id: int) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT subcommand, description FROM subcommands WHERE command_id = ? ORDER BY subcommand",
        (cmd_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _get_options_for(db: DatabaseManager, cmd_id: int) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT flag, description FROM options WHERE command_id = ? ORDER BY flag",
        (cmd_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _exact_name_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE name = ?",
        (query,),
    )
    result = [dict(row) for row in cursor.fetchall()]
    for r in result:
        r["_match_type"] = "exact"
    return result


def _prefix_name_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE name LIKE ? LIMIT 10",
        (f"{query}%",),
    )
    result = [dict(row) for row in cursor.fetchall()]
    for r in result:
        r["_match_type"] = "prefix"
    return result


def _alias_name_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    cursor = db.execute(
        """SELECT c.id, c.name, c.short_description, c.category, c.difficulty, c.risk_level
           FROM commands c JOIN aliases a ON c.id = a.command_id
           WHERE a.alias = ? LIMIT 5""",
        (query,),
    )
    result = [dict(row) for row in cursor.fetchall()]
    for r in result:
        r["_match_type"] = "alias"
    return result


def _contains_name_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    like = f"%{query}%"
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE name LIKE ? LIMIT 10",
        (like,),
    )
    result = [dict(row) for row in cursor.fetchall()]
    for r in result:
        r["_match_type"] = "contains"
    return result


def _keyword_name_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    like = f"%{query}%"
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE keywords LIKE ? LIMIT 10",
        (like,),
    )
    result = [dict(row) for row in cursor.fetchall()]
    for r in result:
        r["_match_type"] = "keyword"
    return result


def _fuzzy_name_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    names = get_all_command_names()
    if HAS_RAPIDFUZZ:
        raw = process.extract(
            query, names, scorer=fuzz.WRatio, score_cutoff=60, limit=5
        )
        matches = [(name, int(score)) for name, score, _ in raw]
    else:
        from shellsense.knowledge.fuzzy import fuzzy_search, spell_correct

        matches = fuzzy_search(query, names)
        if not matches:
            corrections = spell_correct(query)
            if corrections:
                matches = corrections
    if not matches:
        return []
    match_names = [m[0] for m in matches[:5]]
    placeholders = ",".join("?" for _ in match_names)
    cursor = db.execute(
        f"""SELECT id, name, short_description, category, difficulty, risk_level
            FROM commands WHERE name IN ({placeholders})""",
        tuple(match_names),
    )
    rows: dict[str, dict[str, object]] = {
        str(row["name"]): dict(row) for row in cursor.fetchall()
    }
    fuzzy_scores = dict(matches[:5])
    result: list[dict[str, object]] = []
    for name in match_names:
        if name in rows:
            row = rows[name]
            row["_match_type"] = "fuzzy"
            row["_fuzzy_score"] = fuzzy_scores.get(name, 0)
            result.append(row)
    return result


def _suggest_discovered(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    from shellsense.knowledge.discovery_loader import search_discovered

    results = search_discovered(db, query, limit=10)
    for r in results:
        r["_match_type"] = "discovered"
    return results


def invalidate_suggestion_cache() -> None:
    _suggestion_cache.clear()
    logger.info("Suggestion cache invalidated")
