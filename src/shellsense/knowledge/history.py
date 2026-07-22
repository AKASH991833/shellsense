from __future__ import annotations

from typing import Any

from shellsense.database.manager import DatabaseManager
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


def record_search(db: DatabaseManager, query: str, result_count: int = 0) -> None:
    db.execute(
        "INSERT INTO search_history (query, result_count) VALUES (?, ?)",
        (query, result_count),
    )
    db.commit()


def record_suggestion(
    db: DatabaseManager,
    query: str,
    suggestion: str,
    rank: int = 0,
    confidence: float = 0.0,
    source: str = "",
) -> None:
    db.execute(
        "INSERT INTO suggestion_history (query, suggestion, rank, confidence, source) VALUES (?, ?, ?, ?, ?)",
        (query, suggestion, rank, confidence, source),
    )
    db.commit()


def record_explanation(db: DatabaseManager, command: str) -> None:
    db.execute(
        "INSERT INTO explanation_history (command) VALUES (?)",
        (command,),
    )
    db.commit()


def record_usage(
    db: DatabaseManager,
    command_name: str,
    category: str = "",
) -> None:
    cursor = db.execute(
        "SELECT id FROM usage_stats WHERE command_name = ?",
        (command_name,),
    )
    row = cursor.fetchone()
    if row:
        db.execute(
            """UPDATE usage_stats
               SET search_count = search_count + 1, last_used = CURRENT_TIMESTAMP
               WHERE command_name = ?""",
            (command_name,),
        )
    else:
        db.execute(
            "INSERT INTO usage_stats (command_name, search_count, category) VALUES (?, 1, ?)",
            (command_name, category),
        )
    db.commit()


def record_learning(
    db: DatabaseManager,
    command_name: str,
    data_type: str = "search",
    metadata: str = "",
) -> None:
    cursor = db.execute(
        "SELECT id, frequency FROM learning_data WHERE command_name = ? AND data_type = ?",
        (command_name, data_type),
    )
    row = cursor.fetchone()
    if row:
        db.execute(
            "UPDATE learning_data SET frequency = frequency + 1, last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
            (row["id"],),
        )
    else:
        db.execute(
            "INSERT INTO learning_data (command_name, frequency, data_type, metadata) VALUES (?, 1, ?, ?)",
            (command_name, data_type, metadata),
        )
    db.commit()


def get_search_history(db: DatabaseManager, limit: int = 50) -> list[dict[str, Any]]:
    cursor = db.execute(
        "SELECT * FROM search_history ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_suggestion_history(
    db: DatabaseManager, limit: int = 50
) -> list[dict[str, Any]]:
    cursor = db.execute(
        "SELECT * FROM suggestion_history ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_explanation_history(
    db: DatabaseManager, limit: int = 50
) -> list[dict[str, Any]]:
    cursor = db.execute(
        "SELECT * FROM explanation_history ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_usage_stats(db: DatabaseManager, limit: int = 50) -> list[dict[str, Any]]:
    cursor = db.execute(
        "SELECT * FROM usage_stats ORDER BY search_count DESC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_learning_data(
    db: DatabaseManager,
    data_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if data_type:
        cursor = db.execute(
            "SELECT * FROM learning_data WHERE data_type = ? ORDER BY frequency DESC LIMIT ?",
            (data_type, limit),
        )
    else:
        cursor = db.execute(
            "SELECT * FROM learning_data ORDER BY frequency DESC LIMIT ?",
            (limit,),
        )
    return [dict(row) for row in cursor.fetchall()]


def get_popularity_for(db: DatabaseManager, command_name: str) -> int:
    cursor = db.execute(
        "SELECT search_count FROM usage_stats WHERE command_name = ?",
        (command_name,),
    )
    row = cursor.fetchone()
    return row["search_count"] if row else 0


def get_history_frequency_for(db: DatabaseManager, command_name: str) -> int:
    cursor = db.execute(
        "SELECT SUM(frequency) as freq FROM learning_data WHERE command_name = ?",
        (command_name,),
    )
    row = cursor.fetchone()
    if row:
        val = row["freq"]
        return int(val) if val is not None else 0
    return 0


def clear_search_history(db: DatabaseManager) -> None:
    db.execute("DELETE FROM search_history")
    db.commit()
    logger.info("Search history cleared")


def clear_suggestion_history(db: DatabaseManager) -> None:
    db.execute("DELETE FROM suggestion_history")
    db.commit()
    logger.info("Suggestion history cleared")


def clear_explanation_history(db: DatabaseManager) -> None:
    db.execute("DELETE FROM explanation_history")
    db.commit()
    logger.info("Explanation history cleared")


def clear_all_history(db: DatabaseManager) -> None:
    clear_search_history(db)
    clear_suggestion_history(db)
    clear_explanation_history(db)
    db.execute("DELETE FROM learning_data")
    db.commit()
    logger.info("All history cleared")


def get_history_summary(db: DatabaseManager) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table, label in [
        ("search_history", "searches"),
        ("suggestion_history", "suggestions"),
        ("explanation_history", "explanations"),
        ("learning_data", "learning_entries"),
        ("command_history", "commands"),
    ]:
        cursor = db.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        row = cursor.fetchone()
        if row:
            val = row["cnt"]
            counts[label] = int(val) if val is not None else 0
        else:
            counts[label] = 0
    return counts


def search_history(
    db: DatabaseManager,
    query: str,
    limit: int = 10,
) -> list[dict[str, object]]:
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        cursor = db.execute(
            "SELECT DISTINCT command FROM command_history WHERE command LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    cursor = db.execute(
        "SELECT command, COUNT(*) as frequency FROM command_history GROUP BY command ORDER BY frequency DESC LIMIT 200"
    )
    rows = cursor.fetchall()
    commands = [str(row["command"]) for row in rows if row["command"]]
    if not commands:
        return []

    scores = process.extract(query, commands, scorer=fuzz.WRatio, limit=limit)
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for text, score, _ in scores:
        if text not in seen:
            seen.add(text)
            freq = 0
            for row in rows:
                if str(row["command"]) == text:
                    freq = int(row["frequency"]) if row["frequency"] else 0
                    break
            result.append(
                {
                    "command": text,
                    "frequency": freq,
                    "score": score,
                }
            )
    return result
