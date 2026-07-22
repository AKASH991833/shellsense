from shellsense.knowledge.dataset import get_categories, get_command_names, get_commands


class TestDataset:
    def test_get_commands_returns_list(self) -> None:
        cmds = get_commands()
        assert len(cmds) >= 50
        assert all("name" in c for c in cmds)
        assert all("category" in c for c in cmds)

    def test_no_duplicate_names(self) -> None:
        names = get_command_names()
        assert len(names) == len(set(names))

    def test_categories_populated(self) -> None:
        cats = get_categories()
        assert "files" in cats
        assert "networking" in cats
        assert "git" in cats
        assert "docker" in cats

    def test_commands_have_required_fields(self) -> None:
        required = {
            "name",
            "short_description",
            "syntax",
            "category",
            "risk_level",
            "difficulty",
        }
        for cmd in get_commands():
            for field in required:
                assert field in cmd, f"Missing {field} in {cmd.get('name')}"

    def test_risk_levels_valid(self) -> None:
        valid = {"SAFE", "CAUTION", "DANGEROUS", "VERY_DANGEROUS"}
        for cmd in get_commands():
            assert cmd["risk_level"] in valid, f"Invalid risk in {cmd['name']}"
