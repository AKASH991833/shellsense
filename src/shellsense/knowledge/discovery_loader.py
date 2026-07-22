from __future__ import annotations

import json
from typing import Any

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.discovery import discover_all, discover_command
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


def seed_discovered(db: DatabaseManager, max_commands: int = 500) -> int:
    discovered = discover_all(max_commands=max_commands)
    count = 0
    logger.info("Seeding %d discovered commands into database", len(discovered))
    for cmd in discovered:
        try:
            cursor = db.execute(
                "SELECT id FROM commands WHERE name = ?", (cmd["name"],)
            )
            if cursor.fetchone():
                continue
            cursor = db.execute(
                "SELECT id FROM discovered_commands WHERE name = ?", (cmd["name"],)
            )
            if cursor.fetchone():
                db.execute(
                    """UPDATE discovered_commands
                       SET short_description=?, long_description=?, syntax=?,
                           category=?, keywords=?, tags=?, options_json=?,
                           binary_path=?, source=?, last_verified=CURRENT_TIMESTAMP
                       WHERE name=?""",
                    (
                        cmd["short_description"],
                        cmd["long_description"],
                        cmd["syntax"],
                        cmd["category"],
                        cmd["keywords"],
                        ",".join(cmd.get("tags", [])),
                        json.dumps(cmd.get("options", [])),
                        cmd.get("binary_path", ""),
                        "man",
                        cmd["name"],
                    ),
                )
                count += 1
                continue
            db.execute(
                """INSERT INTO discovered_commands
                   (name, short_description, long_description, syntax,
                    category, difficulty, risk_level, availability,
                    keywords, tags, options_json, binary_path, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cmd["name"],
                    cmd["short_description"],
                    cmd["long_description"],
                    cmd["syntax"],
                    cmd["category"],
                    cmd.get("difficulty", "intermediate"),
                    cmd.get("risk_level", "SAFE"),
                    cmd.get("availability", "linux"),
                    cmd.get("keywords", cmd["name"]),
                    ",".join(cmd.get("tags", [])),
                    json.dumps(cmd.get("options", [])),
                    cmd.get("binary_path", ""),
                    "man",
                ),
            )
            count += 1
        except Exception as e:
            logger.error("Failed to seed discovered '%s': %s", cmd["name"], e)
    db.commit()
    logger.info("Discovered %d new commands from system", count)
    return count


def refresh_discovered(db: DatabaseManager, names: list[str] | None = None) -> int:
    if names is None:
        cursor = db.execute("SELECT name FROM discovered_commands")
        names = [str(row["name"]) for row in cursor.fetchall()]
    count = 0
    for name in names:
        cmd = discover_command(name)
        if cmd:
            try:
                db.execute(
                    """UPDATE discovered_commands
                       SET short_description=?, long_description=?, syntax=?,
                           category=?, keywords=?, tags=?, options_json=?,
                           binary_path=?, source=?, last_verified=CURRENT_TIMESTAMP
                       WHERE name=?""",
                    (
                        cmd["short_description"],
                        cmd["long_description"],
                        cmd["syntax"],
                        cmd["category"],
                        cmd["keywords"],
                        ",".join(cmd.get("tags", [])),
                        json.dumps(cmd.get("options", [])),
                        cmd.get("binary_path", ""),
                        "man",
                        name,
                    ),
                )
                count += 1
            except Exception as e:
                logger.error("Failed to refresh '%s': %s", name, e)
    db.commit()
    return count


def get_discovered_count(db: DatabaseManager) -> int:
    cursor = db.execute("SELECT COUNT(*) FROM discovered_commands")
    return int(cursor.fetchone()[0])


def get_discovered_categories(db: DatabaseManager) -> list[dict[str, Any]]:
    cursor = db.execute(
        "SELECT category, COUNT(*) as count FROM discovered_commands GROUP BY category ORDER BY category"
    )
    return [dict(row) for row in cursor.fetchall()]


def search_discovered(
    db: DatabaseManager,
    query: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    if not query:
        cursor = db.execute(
            "SELECT * FROM discovered_commands ORDER BY name LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
    results: list[dict[str, Any]] = []
    cursor = db.execute(
        "SELECT * FROM discovered_commands WHERE name = ?",
        (query,),
    )
    results.extend(dict(row) for row in cursor.fetchall())
    cursor = db.execute(
        "SELECT * FROM discovered_commands WHERE name LIKE ? LIMIT 10",
        (f"{query}%",),
    )
    results.extend(dict(row) for row in cursor.fetchall())
    cursor = db.execute(
        "SELECT * FROM discovered_commands WHERE name LIKE ? OR short_description LIKE ? LIMIT 10",
        (f"%{query}%", f"%{query}%"),
    )
    results.extend(dict(row) for row in cursor.fetchall())
    cursor = db.execute(
        "SELECT * FROM discovered_commands WHERE keywords LIKE ? LIMIT 10",
        (f"%{query}%",),
    )
    results.extend(dict(row) for row in cursor.fetchall())
    from shellsense.knowledge.dataset import get_command_names as get_all_names
    from shellsense.knowledge.fuzzy import fuzzy_search

    names = get_all_names()
    cursor2 = db.execute("SELECT name FROM discovered_commands")
    names.extend(str(r["name"]) for r in cursor2.fetchall())
    matches = fuzzy_search(query, names)
    if matches:
        match_names = [m[0] for m in matches[:5]]
        placeholders = ",".join("?" for _ in match_names)
        cursor = db.execute(
            f"SELECT * FROM discovered_commands WHERE name IN ({placeholders})",
            tuple(match_names),
        )
        results.extend(dict(row) for row in cursor.fetchall())
    seen: set[int] = set()
    unique: list[dict[str, Any]] = []
    for r in results:
        rid = r.get("id")
        if isinstance(rid, int) and rid not in seen:
            seen.add(rid)
            unique.append(r)
    return unique[:limit]


def get_discovered_by_name(db: DatabaseManager, name: str) -> dict[str, Any] | None:
    cursor = db.execute(
        "SELECT * FROM discovered_commands WHERE name = ?",
        (name,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None
