from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.search import search_by_category
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class ContextEngine:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._previous_command: str = ""
        self._current_command: str = ""
        self._session_category: str = ""

    def set_previous_command(self, cmd: str) -> None:
        self._previous_command = cmd

    def set_current_command(self, cmd: str) -> None:
        self._current_command = cmd

    def set_session_category(self, category: str) -> None:
        self._session_category = category

    @property
    def previous_command(self) -> str:
        return self._previous_command

    @property
    def current_command(self) -> str:
        return self._current_command

    @property
    def session_category(self) -> str:
        return self._session_category

    def get_category_commands(self, limit: int = 10) -> list[dict[str, object]]:
        if not self._session_category:
            return []
        return search_by_category(self._db, self._session_category, limit=limit)

    def get_related_to_previous(self, limit: int = 5) -> list[dict[str, object]]:
        if not self._previous_command:
            return []
        from shellsense.knowledge.recommend import recommend_for_command

        return recommend_for_command(self._db, self._previous_command, limit=limit)

    def infer_category_from_query(self, query: str) -> str:
        from shellsense.knowledge.search import get_command_by_name

        cmd = get_command_by_name(self._db, query)
        if cmd:
            return str(cmd.get("category", ""))
        return ""
