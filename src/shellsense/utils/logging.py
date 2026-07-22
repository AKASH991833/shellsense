import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from shellsense.utils.paths import get_log_path

_default_level = logging.INFO
_file_handler: logging.Handler | None = None
_stream_handler: logging.Handler | None = None


def setup_logging(
    level: int | str = _default_level,
    log_file: str | Path | None = None,
    verbose: bool = False,
) -> None:
    global _file_handler, _stream_handler

    if log_file is None:
        log_file = get_log_path()

    logger = logging.getLogger("shellsense")
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    _file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    _file_handler.setLevel(level)
    _file_handler.setFormatter(formatter)
    logger.addHandler(_file_handler)

    console_level = logging.DEBUG if verbose else logging.WARNING
    _stream_handler = logging.StreamHandler(sys.stderr)
    _stream_handler.setLevel(console_level)
    _stream_handler.setFormatter(formatter)
    logger.addHandler(_stream_handler)

    logger.info("Logging initialized. Log file: %s", log_path)


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(f"shellsense.{name}" if name else "shellsense")
