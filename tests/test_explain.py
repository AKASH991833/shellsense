from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.explain import explain_command
from shellsense.knowledge.loader import seed_database


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_explain.db")
    db.initialize()
    if not db.is_seeded():
        seed_database(db)
    return db


class TestExplain:
    def test_explain_existing_command(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        result = explain_command(db, "chmod")
        assert result is not None
        assert result["name"] == "chmod"
        assert "short_description" in result
        assert "options" in result
        assert "examples" in result
        assert "related_commands" in result
        db.close()

    def test_explain_nonexistent(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        result = explain_command(db, "QQXYZZY_NONEXISTENT_12345_UNIQUE")
        assert result is None
        db.close()

    def test_explain_includes_all_sections(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        result = explain_command(db, "ls")
        assert result is not None
        sections = [
            "name",
            "short_description",
            "long_description",
            "syntax",
            "category",
            "difficulty",
            "risk_level",
            "examples",
            "options",
            "related_commands",
        ]
        for section in sections:
            assert section in result, f"Missing section: {section}"
        db.close()

    def test_explain_through_alias(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        result = explain_command(db, "gunzip")
        assert result is not None
        assert result["name"] == "gzip"
        db.close()
