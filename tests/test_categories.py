from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.categories import list_categories, list_commands_in_category
from shellsense.knowledge.loader import seed_database


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_cats.db")
    db.initialize()
    if not db.is_seeded():
        seed_database(db)
    return db


class TestCategories:
    def test_list_categories(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cats = list_categories(db)
        assert len(cats) >= 5
        assert any(c["category"] == "files" for c in cats)
        db.close()

    def test_commands_in_category(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmds = list_commands_in_category(db, "networking")
        assert len(cmds) >= 3
        for c in cmds:
            assert c["category"] == "networking"
        db.close()

    def test_nonexistent_category(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmds = list_commands_in_category(db, "zzz_invalid")
        assert len(cmds) == 0
        db.close()

    def test_category_names_match(self, tmp_path: Path) -> None:
        from shellsense.knowledge.categories import get_all_category_names

        names = get_all_category_names()
        assert "files" in names
        assert isinstance(names, list)
