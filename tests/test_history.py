from __future__ import annotations

from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge import history as history_mod


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_history.db")
    db.initialize()
    return db


class TestHistory:
    def test_record_search(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        history_mod.record_search(db, "grep", 5)
        history = history_mod.get_search_history(db)
        assert len(history) == 1
        assert history[0]["query"] == "grep"
        db.close()

    def test_record_suggestion(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        history_mod.record_suggestion(db, "sys", "systemctl", rank=1, confidence=0.9)
        history = history_mod.get_suggestion_history(db)
        assert len(history) == 1
        assert history[0]["suggestion"] == "systemctl"
        db.close()

    def test_record_explanation(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        history_mod.record_explanation(db, "ls")
        history = history_mod.get_explanation_history(db)
        assert len(history) == 1
        assert history[0]["command"] == "ls"
        db.close()

    def test_record_usage(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        history_mod.record_usage(db, "grep", category="text")
        history_mod.record_usage(db, "grep", category="text")
        stats = history_mod.get_usage_stats(db)
        assert len(stats) == 1
        assert stats[0]["search_count"] == 2
        db.close()

    def test_record_learning(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        history_mod.record_learning(db, "awk", data_type="search")
        history_mod.record_learning(db, "awk", data_type="search")
        data = history_mod.get_learning_data(db)
        assert len(data) == 1
        assert data[0]["frequency"] == 2
        db.close()

    def test_get_popularity_for(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        pop = history_mod.get_popularity_for(db, "nonexistent")
        assert pop == 0
        history_mod.record_usage(db, "ls")
        pop = history_mod.get_popularity_for(db, "ls")
        assert pop == 1
        db.close()

    def test_get_history_frequency_for(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        freq = history_mod.get_history_frequency_for(db, "nonexistent")
        assert freq == 0
        history_mod.record_learning(db, "sed", data_type="search")
        freq = history_mod.get_history_frequency_for(db, "sed")
        assert freq == 1
        db.close()

    def test_clear_search_history(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        history_mod.record_search(db, "test", 1)
        history_mod.clear_search_history(db)
        history = history_mod.get_search_history(db)
        assert len(history) == 0
        db.close()

    def test_clear_all_history(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        history_mod.record_search(db, "test", 1)
        history_mod.record_explanation(db, "ls")
        history_mod.clear_all_history(db)
        summary = history_mod.get_history_summary(db)
        assert summary["searches"] == 0
        assert summary["explanations"] == 0
        db.close()

    def test_get_history_summary(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        history_mod.record_search(db, "a", 1)
        history_mod.record_search(db, "b", 2)
        history_mod.record_explanation(db, "ls")
        summary = history_mod.get_history_summary(db)
        assert summary["searches"] == 2
        assert summary["explanations"] == 1
        db.close()
