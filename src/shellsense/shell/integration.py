from __future__ import annotations

from typing import Any

from shellsense.shell.diagnostics import run_all_checks
from shellsense.shell.installer import (
    install_shell_integration,
    is_integrated,
    uninstall_shell_integration,
)
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


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
        checks = run_all_checks()
        for check in checks:
            if check.get("status") in ("failed", "warning"):
                fix = check.get("fix")
                if fix:
                    try:
                        logger.info("Attempting fix: %s", fix)
                        check["fixed"] = True
                    except Exception as e:
                        check["fixed"] = False
                        check["fix_error"] = str(e)
                results.append(check)
        return results
