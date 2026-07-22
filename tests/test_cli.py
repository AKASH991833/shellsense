from typer.testing import CliRunner

from shellsense.cli.app import app

runner = CliRunner()


class TestCLI:
    def test_version_command(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "shellsense" in result.stdout.lower()
        assert "1.0.0" in result.stdout

    def test_version_flag(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "shellsense" in result.stdout.lower()

    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Think Less" in result.stdout

    def test_info_command(self) -> None:
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "System Information" in result.stdout

    def test_config_show(self) -> None:
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "Configuration" in result.stdout

    def test_config_get(self) -> None:
        result = runner.invoke(app, ["config", "get", "general.theme"])
        assert result.exit_code == 0
        assert "default" in result.stdout

    def test_config_get_nonexistent(self) -> None:
        result = runner.invoke(app, ["config", "get", "nonexistent.key"])
        assert result.exit_code == 1

    def test_config_set(self) -> None:
        result = runner.invoke(app, ["config", "set", "general.theme", "dark"])
        assert result.exit_code == 0
        assert "dark" in result.stdout

    def test_config_path(self) -> None:
        result = runner.invoke(app, ["config", "path"])
        assert result.exit_code == 0
        assert "config.json" in result.stdout

    def test_config_reset(self) -> None:
        result = runner.invoke(app, ["config", "reset"])
        assert result.exit_code == 0

    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        assert result.exit_code == 0 or result.exit_code == 2
        assert "Usage:" in result.stdout or "Commands:" in result.stdout
