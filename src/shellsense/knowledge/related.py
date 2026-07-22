from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.search import (
    get_command_by_name,
    get_related_for_command,
)
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


def get_related_commands(
    db: DatabaseManager, command_name: str
) -> list[dict[str, object]] | None:
    cmd = get_command_by_name(db, command_name)
    if cmd is None:
        return None
    cmd_id = cmd["id"]
    if not isinstance(cmd_id, int):
        return []
    related = get_related_for_command(db, cmd_id)
    enriched: list[dict[str, object]] = []
    for rel in related:
        rel_name = rel.get("related_command_name", "")
        rel_cmd = get_command_by_name(db, str(rel_name)) if rel_name else None
        enriched.append(
            {
                "name": rel_name,
                "relationship": rel.get("relationship", ""),
                "description": (
                    rel_cmd.get("short_description", "") if rel_cmd else ""
                ),
            }
        )
    return enriched
