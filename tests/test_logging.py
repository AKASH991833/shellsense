from pathlib import Path

from shellsense.utils.logging import get_logger, setup_logging


class TestLogging:
    def test_setup_logging_creates_log_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(level="DEBUG", log_file=str(log_file))
        assert log_file.exists()

    def test_logger_writes_message(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(level="DEBUG", log_file=str(log_file))

        logger = get_logger("test")
        logger.info("Test message")

        content = log_file.read_text()
        assert "Test message" in content
        assert "shellsense.test" in content

    def test_get_logger_returns_correct_name(self) -> None:
        setup_logging(level="INFO", log_file="/tmp/test_shellsense.log")
        logger = get_logger("test-module")
        assert logger.name == "shellsense.test-module"

    def test_log_levels_respected(self, tmp_path: Path) -> None:
        log_file = tmp_path / "test.log"
        setup_logging(level="WARNING", log_file=str(log_file))

        logger = get_logger("test")
        logger.info("Should not appear")
        logger.warning("Should appear")

        content = log_file.read_text()
        assert "Should not appear" not in content
        assert "Should appear" in content
