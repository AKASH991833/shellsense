from shellsense.utils.config import DEFAULT_CONFIG, ConfigManager


class TestConfigManager:
    def test_initialization_creates_default_config(
        self, config_manager: ConfigManager
    ) -> None:
        assert config_manager.get("general.theme") == "default"
        assert config_manager.get("general.language") == "en"

    def test_get_existing_key(self, config_manager: ConfigManager) -> None:
        assert config_manager.get("general.theme") == "default"

    def test_get_nonexistent_key(self, config_manager: ConfigManager) -> None:
        assert config_manager.get("nonexistent.key") is None
        assert config_manager.get("nonexistent.key", "fallback") == "fallback"

    def test_set_and_get(self, config_manager: ConfigManager) -> None:
        config_manager.set("general.theme", "dark")
        assert config_manager.get("general.theme") == "dark"

    def test_set_nested_key(self, config_manager: ConfigManager) -> None:
        config_manager.set("ai.model", "gpt-4")
        assert config_manager.get("ai.model") == "gpt-4"

    def test_all_returns_copy(self, config_manager: ConfigManager) -> None:
        all_config = config_manager.all()
        assert isinstance(all_config, dict)
        assert "general" in all_config

    def test_reset_restores_defaults(self, config_manager: ConfigManager) -> None:
        config_manager.set("general.theme", "dark")
        config_manager.reset()
        assert config_manager.get("general.theme") == DEFAULT_CONFIG["general"]["theme"]

    def test_path_property(self, config_manager: ConfigManager) -> None:
        assert config_manager.path.endswith("config.json")
