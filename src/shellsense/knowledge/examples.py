from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.search import get_command_by_name, get_examples_for_command


def get_examples(
    db: DatabaseManager, command_name: str
) -> list[dict[str, object]] | None:
    cmd = get_command_by_name(db, command_name)
    if cmd is None:
        return None
    cmd_id = cmd["id"]
    if not isinstance(cmd_id, int):
        return []
    return get_examples_for_command(db, cmd_id)
