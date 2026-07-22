from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.loader import seed_database
from shellsense.knowledge.related import get_related_commands


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_related.db")
    db.initialize()
    if not db.is_seeded():
        seed_database(db)
    return db


class TestRelated:
    def test_related_for_existing(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        related = get_related_commands(db, "grep")
        assert related is not None
        assert len(related) >= 1
        db.close()

    def test_related_nonexistent(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        related = get_related_commands(db, "QQXYZZY_NONEXISTENT_12345_UNIQUE")
        assert related is None
        db.close()

    def test_related_has_names(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        related = get_related_commands(db, "rm")
        assert related is not None
        for r in related:
            assert "name" in r
            assert "relationship" in r
        db.close()
