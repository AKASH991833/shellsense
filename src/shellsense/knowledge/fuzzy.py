from __future__ import annotations

from rapidfuzz import fuzz, process

from shellsense.knowledge.dataset import get_command_names

FUZZY_THRESHOLD = 60


def spell_correct(
    query: str, min_score: int = FUZZY_THRESHOLD
) -> list[tuple[str, int]]:
    if not query:
        return []
    candidates = get_command_names()
    results = process.extract(
        query, candidates, scorer=fuzz.WRatio, score_cutoff=min_score, limit=5
    )
    return [(name, int(score)) for name, score, _ in results]


def fuzzy_search(
    query: str, candidates: list[str], min_score: int = FUZZY_THRESHOLD
) -> list[tuple[str, int]]:
    if not query:
        return [(c, 0) for c in candidates]
    results = process.extract(
        query, candidates, scorer=fuzz.WRatio, score_cutoff=min_score, limit=10
    )
    return [(name, int(score)) for name, score, _ in results]


def fuzzy_score(a: str, b: str) -> int:
    return int(fuzz.WRatio(a, b))


def best_match(
    query: str, candidates: list[str], min_score: int = FUZZY_THRESHOLD
) -> str | None:
    if not query or not candidates:
        return None
    result = process.extractOne(
        query, candidates, scorer=fuzz.WRatio, score_cutoff=min_score
    )
    if result:
        return result[0]
    return None
