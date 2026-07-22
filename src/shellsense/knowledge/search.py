from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.dataset import get_command_names as get_all_command_names
from shellsense.knowledge.discovery_loader import search_discovered
from shellsense.knowledge.fuzzy import fuzzy_search, spell_correct
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


def search_commands(
    db: DatabaseManager,
    query: str,
    limit: int = 20,
) -> list[dict[str, object]]:
    if not query:
        seeded = list_all(db, limit)
        discovered = search_discovered(db, "", limit)
        return _merge_results(seeded, discovered)[:limit]

    results: list[dict[str, object]] = []

    results.extend(_exact_search(db, query))
    results.extend(_prefix_search(db, query))
    results.extend(_contains_search(db, query))
    results.extend(_alias_search(db, query))
    results.extend(_keyword_search(db, query))
    results.extend(_fuzzy_search(db, query))

    seen: set[int] = set()
    unique: list[dict[str, object]] = []
    for r in results:
        rid = r.get("id")
        if isinstance(rid, int) and rid not in seen:
            seen.add(rid)
            unique.append(r)

    discovered = search_discovered(db, query, limit)
    discovered_result = _merge_results(unique, discovered)

    return discovered_result[:limit]


def _merge_results(
    seeded: list[dict[str, object]],
    discovered: list[dict[str, object]],
) -> list[dict[str, object]]:
    seen_names: set[str] = set()
    merged: list[dict[str, object]] = []
    for r in seeded:
        name = str(r.get("name", ""))
        seen_names.add(name)
        merged.append(r)
    for r in discovered:
        name = str(r.get("name", ""))
        if name not in seen_names:
            seen_names.add(name)
            merged.append(r)
    return merged


def search_by_category(
    db: DatabaseManager, category: str, limit: int = 50
) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE category = ? ORDER BY name",
        (category,),
    )
    return [dict(row) for row in cursor.fetchall()][:limit]


def get_categories(db: DatabaseManager) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT category, COUNT(*) as count FROM commands GROUP BY category ORDER BY category"
    )
    seeded = [dict(row) for row in cursor.fetchall()]
    cursor = db.execute(
        "SELECT category, COUNT(*) as count FROM discovered_commands GROUP BY category ORDER BY category"
    )
    discovered = [dict(row) for row in cursor.fetchall()]
    cat_map: dict[str, int] = {}
    for c in seeded:
        cat_map[str(c["category"])] = int(c["count"])
    for c in discovered:
        cat_name = str(c["category"])
        cat_map[cat_name] = cat_map.get(cat_name, 0) + int(c["count"])
    return [{"category": k, "count": v} for k, v in sorted(cat_map.items())]


def list_all(db: DatabaseManager, limit: int = 50) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands ORDER BY name LIMIT ?",
        (limit,),
    )
    seeded = [dict(row) for row in cursor.fetchall()]
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM discovered_commands ORDER BY name LIMIT ?",
        (limit,),
    )
    discovered = [dict(row) for row in cursor.fetchall()]
    return _merge_results(seeded, discovered)[:limit]


def _exact_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE name = ?",
        (query,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _prefix_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE name LIKE ? LIMIT 10",
        (f"{query}%",),
    )
    return [dict(row) for row in cursor.fetchall()]


def _contains_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE name LIKE ? OR short_description LIKE ? LIMIT 10",
        (f"%{query}%", f"%{query}%"),
    )
    return [dict(row) for row in cursor.fetchall()]


def _alias_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    cursor = db.execute(
        """SELECT c.id, c.name, c.short_description, c.category, c.difficulty, c.risk_level
           FROM commands c JOIN aliases a ON c.id = a.command_id
           WHERE a.alias = ? LIMIT 5""",
        (query,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _keyword_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    like = f"%{query}%"
    cursor = db.execute(
        "SELECT id, name, short_description, category, difficulty, risk_level FROM commands WHERE keywords LIKE ? LIMIT 10",
        (like,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _fuzzy_search(db: DatabaseManager, query: str) -> list[dict[str, object]]:
    names = get_all_command_names()
    matches = fuzzy_search(query, names)
    if not matches:
        corrections = spell_correct(query)
        if corrections:
            matches = corrections
    if not matches:
        return []
    match_names = [m[0] for m in matches[:5]]
    if not match_names:
        return []
    placeholders = ",".join("?" for _ in match_names)
    cursor = db.execute(
        f"""SELECT id, name, short_description, category, difficulty, risk_level
            FROM commands WHERE name IN ({placeholders})""",
        tuple(match_names),
    )
    rows = {str(row["name"]): dict(row) for row in cursor.fetchall()}
    ordered: list[dict[str, object]] = []
    for name in match_names:
        if name in rows:
            ordered.append(rows[name])
    return ordered


def get_command_by_name(db: DatabaseManager, name: str) -> dict[str, object] | None:
    cursor = db.execute(
        "SELECT * FROM commands WHERE name = ?",
        (name,),
    )
    row = cursor.fetchone()
    if row is None:
        cursor = db.execute(
            """SELECT c.* FROM commands c
               JOIN aliases a ON c.id = a.command_id
               WHERE a.alias = ?""",
            (name,),
        )
        row = cursor.fetchone()
    if row is None:
        corrections = spell_correct(name)
        if corrections:
            cursor = db.execute(
                "SELECT * FROM commands WHERE name = ?",
                (corrections[0][0],),
            )
            row = cursor.fetchone()
    if row is None:
        from shellsense.knowledge.discovery_loader import get_discovered_by_name

        discovered = get_discovered_by_name(db, name)
        if discovered:
            return discovered
    return dict(row) if row else None


def get_examples_for_command(
    db: DatabaseManager, command_id: int
) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT * FROM examples WHERE command_id = ?",
        (command_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_related_for_command(
    db: DatabaseManager, command_id: int
) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT * FROM related_commands WHERE command_id = ?",
        (command_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_options_for_command(
    db: DatabaseManager, command_id: int
) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT * FROM options WHERE command_id = ?",
        (command_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_errors_for_command(
    db: DatabaseManager, command_id: int
) -> list[dict[str, object]]:
    cursor = db.execute(
        "SELECT * FROM common_errors WHERE command_id = ?",
        (command_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_aliases_for_command(db: DatabaseManager, command_id: int) -> list[str]:
    cursor = db.execute(
        "SELECT alias FROM aliases WHERE command_id = ?",
        (command_id,),
    )
    return [str(row["alias"]) for row in cursor.fetchall()]


def get_tags_for_command(db: DatabaseManager, command_id: int) -> list[str]:
    cursor = db.execute(
        "SELECT tag FROM tags WHERE command_id = ?",
        (command_id,),
    )
    return [str(row["tag"]) for row in cursor.fetchall()]
