from __future__ import annotations

from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.context import ContextEngine
from shellsense.knowledge.loader import seed_database


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_context.db")
    db.initialize()
    seed_database(db)
    return db


class TestContextEngine:
    def test_set_previous_command(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        ctx = ContextEngine(db)
        ctx.set_previous_command("grep")
        assert ctx.previous_command == "grep"
        db.close()

    def test_set_current_command(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        ctx = ContextEngine(db)
        ctx.set_current_command("awk")
        assert ctx.current_command == "awk"
        db.close()

    def test_set_session_category(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        ctx = ContextEngine(db)
        ctx.set_session_category("text")
        assert ctx.session_category == "text"
        db.close()

    def test_infer_category(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        ctx = ContextEngine(db)
        cat = ctx.infer_category_from_query("grep")
        assert cat == "text"
        db.close()

    def test_infer_category_nonexistent(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        ctx = ContextEngine(db)
        cat = ctx.infer_category_from_query("QQXYZZY_NONEXISTENT_12345_UNIQUE")
        assert cat == ""
        db.close()
