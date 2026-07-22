from __future__ import annotations

import os
from typing import Any

from shellsense.shell.diagnostics import run_all_checks
from shellsense.shell.installer import (
    install_shell_integration,
    is_integrated,
    uninstall_shell_integration,
)
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import (
    ensure_shellsense_dir,
    get_cache_dir,
    get_conversations_dir,
    get_plugins_dir,
)

logger = get_logger(__name__)


def _ensure_directories() -> dict[str, Any]:
    created = []
    dirs = [
        ensure_shellsense_dir(),
        get_cache_dir(),
        get_cache_dir() / "marketplace",
        get_cache_dir() / "ai_cache",
        get_plugins_dir(),
        get_conversations_dir(),
        ensure_shellsense_dir() / "logs",
    ]
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True, mode=0o700)
            created.append(str(d))
        except Exception as e:
            return {"name": "Create directories", "fixed": False, "fix_error": str(e)}
    return {
        "name": "Create directories",
        "fixed": True,
        "detail": f"Created/verified {len(created)} directories",
    }


def _fix_permissions() -> dict[str, Any]:
    try:
        base = ensure_shellsense_dir()
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in (".json", ".db", ".key", ".keys"):
                path.chmod(0o600)
        return {"name": "File permissions", "fixed": True}
    except Exception as e:
        return {"name": "File permissions", "fixed": False, "fix_error": str(e)}


def _reinstall_shell_integration() -> dict[str, Any]:
    try:
        from shellsense.shell.detect import detect_current_shell

        shell = detect_current_shell()
        if not is_integrated(shell):
            install_shell_integration(shell)
            return {"name": "Shell integration", "fixed": True}
        return {
            "name": "Shell integration",
            "fixed": True,
            "detail": "Already integrated",
        }
    except Exception as e:
        return {"name": "Shell integration", "fixed": False, "fix_error": str(e)}


class ShellIntegrationManager:
    def install(self, shell: str | None = None) -> bool:
        return install_shell_integration(shell)

    def uninstall(self, shell: str | None = None) -> bool:
        return uninstall_shell_integration(shell)

    def is_integrated(self, shell: str | None = None) -> bool:
        return is_integrated(shell)

    def diagnose(self) -> list[dict[str, Any]]:
        return run_all_checks()

    def repair(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        dir_result = _ensure_directories()
        results.append(dir_result)

        perm_result = _fix_permissions()
        results.append(perm_result)

        integ_result = _reinstall_shell_integration()
        results.append(integ_result)

        checks = run_all_checks()
        for check in checks:
            if check.get("status") in ("failed", "warning"):
                if not check.get("fix"):
                    check["fixed"] = True
                results.append(check)

        return results
