from __future__ import annotations

import shutil
from pathlib import Path

from shellsense.core.exceptions import UninstallationError
from shellsense.shell.completion import install_completion
from shellsense.shell.detect import (
    detect_current_shell,
    get_backup_path,
    get_shell_config_path,
    is_os_supported,
)
from shellsense.shell.hooks import get_hook_script
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import ensure_shellsense_dir

logger = get_logger(__name__)


_INTEGRATION_MARKER_START = "# --- ShellSense AI integration start ---"
_INTEGRATION_MARKER_END = "# --- ShellSense AI integration end ---"


def _install_autosuggest_scripts(shell: str) -> None:
    shellsense_dir = ensure_shellsense_dir()
    script_src = Path(__file__).parent / "scripts" / f"ss-autosuggest.{shell}"
    if not script_src.exists():
        return
    script_dst = shellsense_dir / f"ss-autosuggest.{shell}"
    shutil.copy2(str(script_src), str(script_dst))
    logger.info("Installed autosuggest script: %s", script_dst)


def _get_integration_block(shell: str) -> str:
    hooks = get_hook_script(shell)
    lines = [
        _INTEGRATION_MARKER_START,
        "# ShellSense AI - Shell Integration",
        "# Do not edit this section manually.",
        "",
        "# Source ShellSense completion",
    ]
    if shell == "bash":
        completion_path = Path.home() / ".shellsense" / "ss-completion.bash"
        lines.append(f"source {completion_path}")
    elif shell == "zsh":
        completion_path = Path.home() / ".shellsense" / "ss-completion.zsh"
        lines.append(f"source {completion_path}")
    elif shell == "fish":
        completion_path = Path.home() / ".shellsense" / "ss-completion.fish"
        lines.append(f"source {completion_path}")

    lines.append("")
    lines.append("# ShellSense autosuggest")
    autosuggest_path = Path.home() / ".shellsense" / f"ss-autosuggest.{shell}"
    if autosuggest_path.exists():
        lines.append(f"source {autosuggest_path}")

    lines.append("")
    lines.append("# ShellSense hooks")
    lines.append(hooks)

    lines.append(_INTEGRATION_MARKER_END)
    return "\n".join(lines) + "\n"


def install_shell_integration(
    shell: str | None = None,
    backup: bool = True,
) -> bool:
    if shell is None:
        shell = detect_current_shell()

    if not is_os_supported():
        logger.warning("OS may not be fully supported")

    config_path = get_shell_config_path(shell)
    if not config_path.parent.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        config_path.touch()

    if backup:
        _backup_config(config_path)

    install_completion(shell)
    _install_autosuggest_scripts(shell)

    integration_block = _get_integration_block(shell)
    content = config_path.read_text()

    if _INTEGRATION_MARKER_START in content:
        start = content.find(_INTEGRATION_MARKER_START)
        end = content.find(_INTEGRATION_MARKER_END, start)
        if end != -1:
            end += len(_INTEGRATION_MARKER_END)
            content = content[:start] + content[end:]
        content = content.rstrip() + "\n\n" + integration_block
    else:
        content = content.rstrip() + "\n\n" + integration_block

    config_path.write_text(content)
    logger.info("Shell integration installed for %s in %s", shell, config_path)
    return True


def uninstall_shell_integration(
    shell: str | None = None,
    restore_backup: bool = True,
) -> bool:
    if shell is None:
        shell = detect_current_shell()

    config_path = get_shell_config_path(shell)
    if not config_path.exists():
        raise UninstallationError(f"Config file not found: {config_path}")

    content = config_path.read_text()

    if _INTEGRATION_MARKER_START in content:
        start = content.find(_INTEGRATION_MARKER_START)
        end = content.find(_INTEGRATION_MARKER_END, start)
        if end != -1:
            end += len(_INTEGRATION_MARKER_END)
            new_content = content[:start] + content[end:]
            new_content = new_content.strip() + "\n"
            config_path.write_text(new_content)
            logger.info("Removed integration block from %s", config_path)
        else:
            logger.warning("Integration marker end not found in %s", config_path)
            return False

    completion_dir = Path.home() / ".shellsense"
    for ext in [".bash", ".zsh", ".fish"]:
        comp_file = completion_dir / f"ss-completion{ext}"
        if comp_file.exists():
            comp_file.unlink()
            logger.info("Removed completion script: %s", comp_file)
        autosuggest_file = completion_dir / f"ss-autosuggest{ext}"
        if autosuggest_file.exists():
            autosuggest_file.unlink()
            logger.info("Removed autosuggest script: %s", autosuggest_file)

    if restore_backup:
        backup_path = get_backup_path(config_path)
        if backup_path.exists():
            shutil.copy2(backup_path, config_path)
            logger.info("Restored backup: %s", backup_path)

    logger.info("Shell integration uninstalled for %s", shell)
    return True


def is_integrated(shell: str | None = None) -> bool:
    if shell is None:
        shell = detect_current_shell()
    config_path = get_shell_config_path(shell)
    if not config_path.exists():
        return False
    content = config_path.read_text()
    return _INTEGRATION_MARKER_START in content


def _backup_config(filepath: Path) -> Path | None:
    backup_path = get_backup_path(filepath)
    if not backup_path.exists():
        shutil.copy2(filepath, backup_path)
        logger.info("Backup created: %s", backup_path)
        return backup_path
    return None
