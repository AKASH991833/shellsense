from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge import (
    categories as categories_mod,
)
from shellsense.knowledge import (
    examples as examples_mod,
)
from shellsense.knowledge import (
    explain as explain_mod,
)
from shellsense.knowledge import (
    history as history_mod,
)
from shellsense.knowledge import (
    loader,
)
from shellsense.knowledge import (
    recommend as recommend_mod,
)
from shellsense.knowledge import (
    related as related_mod,
)
from shellsense.knowledge import (
    search as search_mod,
)
from shellsense.knowledge import (
    suggest as suggest_mod,
)
from shellsense.knowledge.context import ContextEngine
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class KnowledgeEngine:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._context = ContextEngine(db)

    def seed(self) -> int:
        return loader.seed_database(self._db)

    def search(self, query: str, limit: int = 20) -> list[dict[str, object]]:
        logger.info("Search: %s", query)
        return search_mod.search_commands(self._db, query, limit=limit)

    def explain(self, name: str) -> dict[str, object] | None:
        logger.info("Explain: %s", name)
        return explain_mod.explain_command(self._db, name)

    def examples(self, name: str) -> list[dict[str, object]] | None:
        logger.info("Examples: %s", name)
        return examples_mod.get_examples(self._db, name)

    def list_categories(self) -> list[dict[str, object]]:
        logger.info("Categories: list")
        return categories_mod.list_categories(self._db)

    def commands_in_category(self, category: str) -> list[dict[str, object]]:
        logger.info("Category: %s", category)
        return categories_mod.list_commands_in_category(self._db, category)

    def related(self, name: str) -> list[dict[str, object]] | None:
        logger.info("Related: %s", name)
        return related_mod.get_related_commands(self._db, name)

    def suggest(self, query: str, limit: int = 10) -> list[dict[str, object]]:
        logger.info("Suggest: %s", query)
        return suggest_mod.suggest_commands(
            self._db, query, limit=limit, context=self._context
        )

    def predict(self, partial: str, limit: int = 10) -> list[dict[str, object]]:
        logger.info("Predict: %s", partial)
        return suggest_mod.predict_commands(self._db, partial, limit=limit)

    def recommend(self, command_name: str, limit: int = 10) -> list[dict[str, object]]:
        logger.info("Recommend: %s", command_name)
        return recommend_mod.recommend_for_command(self._db, command_name, limit=limit)

    def similar(self, command_name: str, limit: int = 10) -> list[dict[str, object]]:
        logger.info("Similar: %s", command_name)
        return recommend_mod.find_similar_commands(self._db, command_name, limit=limit)

    def get_history(self, limit: int = 50) -> list[dict[str, object]]:
        logger.info("History: list")
        return history_mod.get_search_history(self._db, limit=limit)

    def clear_history(self) -> None:
        logger.info("History: clear")
        history_mod.clear_all_history(self._db)

    def get_history_summary(self) -> dict[str, int]:
        return history_mod.get_history_summary(self._db)

    def record_search(self, query: str, result_count: int = 0) -> None:
        history_mod.record_search(self._db, query, result_count)

    def record_explanation(self, command: str) -> None:
        history_mod.record_explanation(self._db, command)

    def record_usage(self, command_name: str, category: str = "") -> None:
        history_mod.record_usage(self._db, command_name, category)

    def invalidate_suggestion_cache(self) -> None:
        suggest_mod.invalidate_suggestion_cache()

    def discover(self, max_commands: int = 500) -> int:
        from shellsense.knowledge.discovery_loader import seed_discovered

        count = seed_discovered(self._db, max_commands=max_commands)
        logger.info("Discovery: added %d commands", count)
        return count

    def refresh_discovery(self, names: list[str] | None = None) -> int:
        from shellsense.knowledge.discovery_loader import refresh_discovered

        count = refresh_discovered(self._db, names)
        logger.info("Discovery refresh: updated %d commands", count)
        return count

    def get_discovery_count(self) -> int:
        from shellsense.knowledge.discovery_loader import get_discovered_count

        return get_discovered_count(self._db)

    def get_discovery_categories(self) -> list[dict[str, object]]:
        from shellsense.knowledge.discovery_loader import get_discovered_categories

        return get_discovered_categories(self._db)

    def learn_from_history(self, history_file: str | None = None) -> int:
        if history_file is None:
            import os

            shell = os.environ.get("SHELL", "")
            home = os.path.expanduser("~")
            if "zsh" in shell:
                history_file = os.path.join(home, ".zsh_history")
            elif "fish" in shell:
                history_file = os.path.join(home, ".local/share/fish/fish_history")
            else:
                history_file = os.path.join(home, ".bash_history")
        try:
            with open(history_file, errors="ignore") as f:
                lines = f.readlines()
        except OSError:
            logger.warning("Cannot read history file: %s", history_file)
            return 0
        count = 0
        from shellsense.knowledge.history import record_usage

        for line in lines[-1000:]:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line and ";" in line:
                parts = line.split(";", 1)
                line = parts[-1].strip()
            cmd = line.split()[0] if line.split() else ""
            if cmd and not cmd.startswith("_"):
                record_usage(self._db, cmd)
                count += 1
        logger.info("Learned %d commands from history", count)
        return count

    @property
    def context(self) -> ContextEngine:
        return self._context

    @property
    def db(self) -> DatabaseManager:
        return self._db
