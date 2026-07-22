from __future__ import annotations

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.dataset import get_categories as get_dataset_categories
from shellsense.knowledge.search import get_categories as search_get_categories
from shellsense.knowledge.search import search_by_category


def list_categories(db: DatabaseManager) -> list[dict[str, object]]:
    return search_get_categories(db)


def list_commands_in_category(
    db: DatabaseManager, category: str
) -> list[dict[str, object]]:
    return search_by_category(db, category)


def get_all_category_names() -> list[str]:
    return get_dataset_categories()
