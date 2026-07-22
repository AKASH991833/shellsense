from __future__ import annotations

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_RANKING_WEIGHTS: dict[str, float] = {
    "exact_match": 100.0,
    "prefix_match": 80.0,
    "alias_match": 70.0,
    "keyword_match": 50.0,
    "contains_match": 40.0,
    "fuzzy_match_multiplier": 0.5,
    "category_match": 20.0,
    "popularity_multiplier": 10.0,
    "history_multiplier": 15.0,
    "command_length_penalty": 0.1,
    "edit_distance_bonus": 50.0,
}


def score_suggestion(
    query: str,
    command_name: str,
    match_type: str,
    fuzzy_score_val: int = 0,
    popularity: int = 0,
    history_freq: int = 0,
    category_bonus: bool = False,
    edit_distance: int | None = None,
    weights: dict[str, float] | None = None,
) -> float:
    w = weights or DEFAULT_RANKING_WEIGHTS
    score = 0.0

    if match_type == "exact":
        score += w.get("exact_match", 100.0)
    elif match_type == "prefix":
        score += w.get("prefix_match", 80.0)
    elif match_type == "alias":
        score += w.get("alias_match", 70.0)
    elif match_type == "keyword":
        score += w.get("keyword_match", 50.0)
    elif match_type == "contains":
        score += w.get("contains_match", 40.0)
    elif match_type == "fuzzy":
        score += fuzzy_score_val * w.get("fuzzy_match_multiplier", 0.5)

    if category_bonus:
        score += w.get("category_match", 20.0)

    if popularity > 0:
        import math

        score += w.get("popularity_multiplier", 10.0) * math.log(popularity + 1)

    if history_freq > 0:
        import math

        score += w.get("history_multiplier", 15.0) * math.log(history_freq + 1)

    penalty = w.get("command_length_penalty", 0.1)
    score -= len(command_name) * penalty

    if edit_distance is not None and edit_distance == 1:
        score += w.get("edit_distance_bonus", 50.0)

    return max(score, 0.0)


def rank_suggestions(
    query: str,
    candidates: list[dict[str, object]],
    query_lower: str = "",
    weights: dict[str, float] | None = None,
    min_score: float = 0.0,
) -> list[dict[str, object]]:
    if not candidates:
        return []

    if not query_lower:
        query_lower = query.lower().strip()

    scored: list[tuple[float, dict[str, object]]] = []
    for cmd in candidates:
        name = str(cmd.get("name", ""))
        name_lower = name.lower()

        match_type_raw = cmd.get("_match_type", "")
        match_type = str(match_type_raw) if match_type_raw else ""
        fuzzy_raw = cmd.get("_fuzzy_score", 0) or 0
        fuzzy_val = int(str(fuzzy_raw))
        pop_raw = cmd.get("_popularity", 0) or 0
        popularity = int(str(pop_raw))
        hist_raw = cmd.get("_history_freq", 0) or 0
        history_freq = int(str(hist_raw))

        if not match_type or match_type == "contains":
            if name_lower == query_lower:
                match_type = "exact"
            elif name_lower.startswith(query_lower):
                match_type = "prefix"
            elif fuzzy_val > 0:
                match_type = "fuzzy"
            else:
                match_type = "contains"

        score = score_suggestion(
            query=query,
            command_name=name,
            match_type=match_type,
            fuzzy_score_val=fuzzy_val,
            popularity=popularity,
            history_freq=history_freq,
            weights=weights,
        )

        if score >= min_score:
            scored.append((score, cmd))

    scored.sort(key=lambda x: (-x[0], x[1].get("name", "")))
    return [cmd for _, cmd in scored]
