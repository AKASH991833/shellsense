from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.loader import seed_database


class TestLoader:
    def test_seed_populates_database(self, tmp_path: Path) -> None:
        db = DatabaseManager(tmp_path / "test_seed.db")
        db.initialize()
        assert not db.is_seeded()
        count = seed_database(db)
        assert count >= 50
        assert db.is_seeded()
        db.close()

    def test_seed_idempotent(self, tmp_path: Path) -> None:
        db = DatabaseManager(tmp_path / "test_seed2.db")
        db.initialize()
        seed_database(db)
        count2 = seed_database(db)
        assert count2 == 0
        db.close()

    def test_seeded_commands_have_all_data(self, tmp_path: Path) -> None:
        db = DatabaseManager(tmp_path / "test_seed3.db")
        db.initialize()
        seed_database(db)
        cursor = db.execute("SELECT COUNT(*) FROM commands")
        assert cursor.fetchone()[0] >= 50
        cursor = db.execute("SELECT COUNT(*) FROM examples")
        assert cursor.fetchone()[0] >= 50
        cursor = db.execute("SELECT COUNT(*) FROM options")
        assert cursor.fetchone()[0] >= 50
        cursor = db.execute("SELECT COUNT(*) FROM aliases")
        assert cursor.fetchone()[0] >= 1
        cursor = db.execute("SELECT COUNT(*) FROM related_commands")
        assert cursor.fetchone()[0] >= 50
        cursor = db.execute("SELECT COUNT(*) FROM common_errors")
        assert cursor.fetchone()[0] >= 1
        cursor = db.execute("SELECT COUNT(*) FROM tags")
        assert cursor.fetchone()[0] >= 50
        db.close()
