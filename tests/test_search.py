from pathlib import Path

from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.loader import seed_database
from shellsense.knowledge.search import (
    get_aliases_for_command,
    get_categories,
    get_command_by_name,
    get_errors_for_command,
    get_examples_for_command,
    get_options_for_command,
    get_related_for_command,
    search_by_category,
    search_commands,
)


def _setup_db(tmp_path: Path) -> DatabaseManager:
    db = DatabaseManager(tmp_path / "test_knowledge.db")
    db.initialize()
    if not db.is_seeded():
        seed_database(db)
    return db


class TestSearch:
    def test_exact_search(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = search_commands(db, "chmod")
        assert len(results) >= 1
        assert results[0]["name"] == "chmod"
        db.close()

    def test_prefix_search(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = search_commands(db, "ch")
        assert len(results) >= 1
        names = [r["name"] for r in results]
        assert any(n.startswith("ch") for n in names)
        db.close()

    def test_search_by_category(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = search_by_category(db, "networking")
        assert len(results) >= 3
        all_networking = all(r["category"] == "networking" for r in results)
        assert all_networking
        db.close()

    def test_empty_query_returns_all(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = search_commands(db, "", limit=10)
        assert len(results) >= 1
        db.close()

    def test_nonexistent_command(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmd = get_command_by_name(db, "QQXYZZY_NONEXISTENT_12345_UNIQUE")
        assert cmd is None
        db.close()

    def test_get_categories(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cats = get_categories(db)
        assert len(cats) >= 5
        assert any(c["category"] == "files" for c in cats)
        db.close()

    def test_get_command_by_name(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmd = get_command_by_name(db, "grep")
        assert cmd is not None
        assert cmd["name"] == "grep"
        db.close()

    def test_get_command_by_alias(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmd = get_command_by_name(db, "gunzip")
        assert cmd is not None
        assert cmd["name"] == "gzip"
        db.close()

    def test_related_commands(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmd = get_command_by_name(db, "grep")
        assert cmd is not None
        cmd_id = cmd["id"]
        if isinstance(cmd_id, int):
            related = get_related_for_command(db, cmd_id)
            assert len(related) >= 1
        db.close()

    def test_examples(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmd = get_command_by_name(db, "tar")
        assert cmd is not None
        cmd_id = cmd["id"]
        if isinstance(cmd_id, int):
            examples = get_examples_for_command(db, cmd_id)
            assert len(examples) >= 2
        db.close()

    def test_options(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmd = get_command_by_name(db, "ls")
        assert cmd is not None
        cmd_id = cmd["id"]
        if isinstance(cmd_id, int):
            options = get_options_for_command(db, cmd_id)
            assert len(options) >= 2
        db.close()

    def test_aliases(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmd = get_command_by_name(db, "tar")
        assert cmd is not None
        cmd_id = cmd["id"]
        if isinstance(cmd_id, int):
            aliases = get_aliases_for_command(db, cmd_id)
            assert isinstance(aliases, list)
        db.close()

    def test_common_errors(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        cmd = get_command_by_name(db, "ssh")
        assert cmd is not None
        cmd_id = cmd["id"]
        if isinstance(cmd_id, int):
            errors = get_errors_for_command(db, cmd_id)
            assert len(errors) >= 1
        db.close()

    def test_fuzzy_search_spelling(self, tmp_path: Path) -> None:
        db = _setup_db(tmp_path)
        results = search_commands(db, "sytemctl")
        assert len(results) >= 1
        assert results[0]["name"] == "systemctl"
        db.close()
