from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.search import (
    get_aliases_for_command,
    get_command_by_name,
    get_errors_for_command,
    get_examples_for_command,
    get_options_for_command,
    get_related_for_command,
)
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


def explain_command(db: DatabaseManager, name: str) -> dict[str, object] | None:
    cmd = get_command_by_name(db, name)
    if cmd is None:
        return None

    cmd_id = cmd["id"]
    if isinstance(cmd_id, int):
        cmd["aliases"] = get_aliases_for_command(db, cmd_id)
        cmd["options"] = get_options_for_command(db, cmd_id)
        cmd["examples"] = get_examples_for_command(db, cmd_id)
        cmd["related_commands"] = get_related_for_command(db, cmd_id)
        cmd["common_errors"] = get_errors_for_command(db, cmd_id)
    else:
        cmd["aliases"] = []
        cmd["options"] = []
        cmd["examples"] = []
        cmd["related_commands"] = []
        cmd["common_errors"] = []

    return cmd
