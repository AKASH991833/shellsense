from __future__ import annotations

from pathlib import Path

from shellsense.shell.detect import (
    detect_current_shell,
    get_shell_config_path,
)
from shellsense.shell.hooks import get_prompt_snippet
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


_SS_MARKER_START = "# --- ShellSense AI start ---"
_SS_MARKER_END = "# --- ShellSense AI end ---"


def is_prompt_integrated(shell: str | None = None) -> bool:
    if shell is None:
        shell = detect_current_shell()
    config_path = get_shell_config_path(shell)
    if not config_path.exists():
        return False
    content = config_path.read_text()
    return _SS_MARKER_START in content


def enable_prompt_integration(shell: str | None = None) -> bool:
    if shell is None:
        shell = detect_current_shell()
    if is_prompt_integrated(shell):
        logger.info("Prompt already integrated for %s", shell)
        return True

    snippet = get_prompt_snippet(shell)
    if not snippet:
        logger.warning("No prompt snippet for shell: %s", shell)
        return False

    config_path = get_shell_config_path(shell)
    _append_to_config(config_path, snippet)
    logger.info("Prompt integration enabled for %s", shell)
    return True


def disable_prompt_integration(shell: str | None = None) -> bool:
    if shell is None:
        shell = detect_current_shell()
    config_path = get_shell_config_path(shell)
    if not config_path.exists():
        return False

    content = config_path.read_text()
    if _SS_MARKER_START not in content:
        return True

    start = content.find(_SS_MARKER_START)
    end = content.find(_SS_MARKER_END, start)
    if end != -1:
        end += len(_SS_MARKER_END) + 1
        new_content = content[:start] + content[end:]
        _write_config(config_path, new_content)
    else:
        new_content = content[:start]
        _write_config(config_path, new_content)

    logger.info("Prompt integration disabled for %s", shell)
    return True


def _append_to_config(filepath: Path, snippet: str) -> None:
    backup_path = filepath.with_suffix(filepath.suffix + ".shellsense.bak")
    if not backup_path.exists():
        import shutil

        shutil.copy2(filepath, backup_path)
        logger.info("Backup created: %s", backup_path)

    with filepath.open("a") as f:
        f.write("\n")
        f.write(_SS_MARKER_START + "\n")
        f.write(snippet + "\n")
        f.write(_SS_MARKER_END + "\n")


def _write_config(filepath: Path, content: str) -> None:
    backup_path = filepath.with_suffix(filepath.suffix + ".shellsense.bak")
    if not backup_path.exists():
        import shutil

        shutil.copy2(filepath, backup_path)
        logger.info("Backup created: %s", backup_path)

    filepath.write_text(content)
