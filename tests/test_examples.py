from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.examples import get_examples
from shellsense.knowledge.loader import seed_database


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_examples.db")
    db.initialize()
    if not db.is_seeded():
        seed_database(db)
    return db


class TestExamples:
    def test_get_examples_existing(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        examples = get_examples(db, "tar")
        assert examples is not None
        assert len(examples) >= 2
        db.close()

    def test_get_examples_nonexistent(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        examples = get_examples(db, "QQXYZZY_NONEXISTENT_12345_UNIQUE")
        assert examples is None
        db.close()

    def test_examples_have_required_fields(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        examples = get_examples(db, "grep")
        assert examples is not None
        for ex in examples:
            assert "command" in ex
            assert "title" in ex
        db.close()
