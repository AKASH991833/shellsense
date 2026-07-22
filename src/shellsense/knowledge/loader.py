from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.dataset import get_commands
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


def seed_database(db: DatabaseManager) -> int:
    if db.is_seeded():
        logger.info("Knowledge base already seeded, skipping")
        return 0

    commands = get_commands()
    count = 0
    logger.info("Seeding knowledge base with %d commands", len(commands))

    for cmd in commands:
        try:
            db.execute(
                """INSERT INTO commands
                   (name, short_description, long_description, syntax,
                    category, difficulty, risk_level, availability,
                    official_docs, keywords, notes, warnings)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cmd["name"],
                    cmd["short_description"],
                    cmd["long_description"],
                    cmd["syntax"],
                    cmd["category"],
                    cmd["difficulty"],
                    cmd["risk_level"],
                    cmd["availability"],
                    cmd["official_docs"],
                    cmd["keywords"],
                    cmd["notes"],
                    cmd["warnings"],
                ),
            )
            cmd_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

            for alias in cmd.get("aliases", []):
                db.execute(
                    "INSERT INTO aliases (command_id, alias) VALUES (?, ?)",
                    (cmd_id, alias),
                )

            for ex in cmd.get("examples", []):
                db.execute(
                    """INSERT INTO examples
                       (command_id, title, command, output, description)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        cmd_id,
                        ex.get("title", ""),
                        ex.get("command", ""),
                        ex.get("output", ""),
                        ex.get("description", ""),
                    ),
                )

            for opt in cmd.get("options", []):
                db.execute(
                    "INSERT INTO options (command_id, flag, description) VALUES (?, ?, ?)",
                    (cmd_id, opt.get("flag", ""), opt.get("description", "")),
                )

            for err in cmd.get("common_errors", []):
                db.execute(
                    """INSERT INTO common_errors
                       (command_id, error_pattern, explanation, solution)
                       VALUES (?, ?, ?, ?)""",
                    (
                        cmd_id,
                        err.get("error_pattern", ""),
                        err.get("explanation", ""),
                        err.get("solution", ""),
                    ),
                )

            for rel in cmd.get("related_commands", []):
                db.execute(
                    """INSERT INTO related_commands
                       (command_id, related_command_name, relationship)
                       VALUES (?, ?, ?)""",
                    (cmd_id, rel.get("name", ""), rel.get("relationship", "")),
                )

            for tag in cmd.get("tags", []):
                db.execute(
                    "INSERT INTO tags (command_id, tag) VALUES (?, ?)",
                    (cmd_id, tag),
                )

            count += 1
        except Exception as e:
            logger.error("Failed to seed command '%s': %s", cmd["name"], e)
            continue

    db.commit()
    logger.info("Seeded %d commands into knowledge base", count)
    return count
