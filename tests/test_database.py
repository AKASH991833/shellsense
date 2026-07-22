from pathlib import Path

from shellsense.database.manager import DatabaseManager


class TestDatabaseManager:
    def test_initialize_creates_tables(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db = DatabaseManager(db_path)
        db.initialize()

        conn = db.connect()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        db.close()

        expected_tables = [
            "command_history",
            "command_suggestions",
            "correction_log",
            "error_analysis",
            "learning_entries",
            "schema_version",
        ]
        for table in expected_tables:
            assert table in tables

    def test_execute_and_commit(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db = DatabaseManager(db_path)
        db.initialize()

        db.execute(
            "INSERT INTO command_history (command, exit_code) VALUES (?, ?)",
            ("ls -la", 0),
        )
        db.commit()

        cursor = db.execute("SELECT command FROM command_history")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "ls -la"

        db.close()

    def test_path_property(self, tmp_path: Path) -> None:
        db_path = tmp_path / "custom.db"
        db = DatabaseManager(db_path)
        assert db.path == db_path
        db.close()

    def test_context_manager(self, tmp_path: Path) -> None:
        db_path = tmp_path / "context.db"
        with DatabaseManager(db_path) as db:
            db.initialize()
            assert db.path == db_path

    def test_schema_version(self, tmp_path: Path) -> None:
        db_path = tmp_path / "version.db"
        db = DatabaseManager(db_path)
        db.initialize()

        cursor = db.execute("SELECT MAX(version) FROM schema_version")
        version = cursor.fetchone()[0]
        assert version == 4

        db.close()
