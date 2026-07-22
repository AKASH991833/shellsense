from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class AIContext:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._permission_granted: bool = False

    def grant_permission(self) -> None:
        self._permission_granted = True

    def revoke_permission(self) -> None:
        self._permission_granted = False

    @property
    def has_permission(self) -> bool:
        return self._permission_granted

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def collect_system_context(self) -> dict[str, Any]:
        ctx: dict[str, Any] = {
            "os": platform.system().lower(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
        }
        try:
            ctx["current_directory"] = os.getcwd()
        except Exception:
            ctx["current_directory"] = ""
        try:
            ctx["home_directory"] = str(Path.home())
        except Exception:
            ctx["home_directory"] = ""
        return ctx

    def collect_shell_context(self) -> dict[str, Any]:
        return {
            "shell": os.environ.get("SHELL", ""),
            "terminal": os.environ.get("TERM", ""),
            "user": os.environ.get("USER", ""),
        }

    def collect_git_context(self) -> dict[str, Any]:
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                repo_root = result.stdout.strip()
                branch_result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                branch = (
                    branch_result.stdout.strip()
                    if branch_result.returncode == 0
                    else ""
                )
                return {"git_repo": repo_root, "git_branch": branch}
        except Exception:
            pass
        return {}

    @property
    def context_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def get_context_summary(self) -> str:
        parts: list[str] = []
        os_name = self._data.get("os", "linux")
        parts.append(f"OS: {os_name}")
        shell = self._data.get("shell", "")
        if shell:
            parts.append(f"Shell: {shell}")
        cwd = self._data.get("current_directory", "")
        if cwd:
            parts.append(f"Dir: {cwd}")
        return " | ".join(parts)
