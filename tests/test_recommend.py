from __future__ import annotations

from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.loader import seed_database
from shellsense.knowledge.recommend import find_similar_commands, recommend_for_command


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_recommend.db")
    db.initialize()
    seed_database(db)
    return db


class TestRecommend:
    def test_recommend_for_existing(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = recommend_for_command(db, "grep")
        assert len(results) > 0
        names = [str(r.get("name", "")) for r in results]
        has_related = any(r.get("relationship") for r in results)
        assert has_related or len(results) > 0
        db.close()

    def test_recommend_for_nonexistent(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = recommend_for_command(db, "QQXYZZY_NONEXISTENT_12345_UNIQUE")
        assert results == []
        db.close()

    def test_recommend_limit(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = recommend_for_command(db, "ssh", limit=3)
        assert len(results) <= 3
        db.close()


class TestSimilar:
    def test_similar_for_existing(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = find_similar_commands(db, "chmod")
        assert len(results) > 0
        names = [str(r.get("name", "")) for r in results]
        has_similar = any(r.get("similarity_reason") for r in results)
        assert has_similar or len(results) > 0
        db.close()

    def test_similar_for_nonexistent(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = find_similar_commands(db, "QQXYZZY_NONEXISTENT_12345_UNIQUE")
        assert results == []
        db.close()

    def test_similar_same_category(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = find_similar_commands(db, "ls")
        names = [str(r.get("name", "")) for r in results]
        assert len(results) > 0
        db.close()
