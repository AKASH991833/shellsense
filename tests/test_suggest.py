from __future__ import annotations

from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.loader import seed_database
from shellsense.knowledge.suggest import predict_commands, suggest_commands


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_suggest.db")
    db.initialize()
    seed_database(db)
    return db


class TestSuggest:
    def test_suggest_empty_query(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = suggest_commands(db, "")
        assert len(results) > 0
        db.close()

    def test_suggest_prefix(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = suggest_commands(db, "sys")
        names = [str(r.get("name", "")) for r in results]
        matched = any(n.startswith("sys") for n in names)
        assert matched, f"Expected sys-prefixed commands, got {names}"
        db.close()

    def test_suggest_exact(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = suggest_commands(db, "grep")
        names = [str(r.get("name", "")) for r in results]
        assert "grep" in names
        db.close()

    def test_suggest_limit(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = suggest_commands(db, "a", limit=3)
        assert len(results) <= 3
        db.close()

    def test_suggest_nonexistent(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = suggest_commands(db, "QQXYZZY_NONEXISTENT_12345_UNIQUE")
        assert results is not None
        db.close()


class TestPredict:
    def test_predict_empty(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = predict_commands(db, "")
        assert results == []
        db.close()

    def test_predict_single_word(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = predict_commands(db, "sys")
        assert len(results) > 0
        db.close()

    def test_predict_multi_word(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = predict_commands(db, "systemctl sta")
        names = [str(r.get("name", "")) for r in results]
        systemd_names = [n for n in names if "systemctl" in n]
        assert len(systemd_names) > 0, f"Expected systemctl subcommands, got {names}"
        db.close()
