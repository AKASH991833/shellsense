from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_plugins_dir, get_shellsense_dir

logger = get_logger(__name__)

PERMISSION_GROUPS: dict[str, str] = {
    "filesystem.read": "Read files on the filesystem",
    "filesystem.write": "Write files on the filesystem",
    "network": "Make network requests",
    "ai.access": "Access AI providers",
    "shell.history": "Read shell command history",
    "env.variables": "Access environment variables",
    "system.info": "Access system information",
    "git.access": "Access git repositories",
    "logs.access": "Access system logs",
    "automation.generate": "Use the automation engine",
    "template.manage": "Manage templates",
    "shell.execute": "Execute shell commands",
    "process.list": "List running processes",
    "package.manage": "Access package managers",
}

_ALLOWED_BASE = Path(get_shellsense_dir())


def is_path_allowed(requested_path: str) -> bool:
    resolved = Path(requested_path).resolve()
    return _ALLOWED_BASE in resolved.parents or resolved == _ALLOWED_BASE


def sanitize_path(requested_path: str) -> str:
    resolved = Path(requested_path).resolve()
    if not is_path_allowed(str(resolved)):
        raise PermissionError(
            f"Path '{requested_path}' is outside ShellSense directory "
            f"({_ALLOWED_BASE})"
        )
    return str(resolved)


class PermissionManager:
    def __init__(self) -> None:
        self._grants: dict[str, set[str]] = {}
        self._load()

    def _grants_path(self) -> str:
        return os.path.join(get_plugins_dir(), "permissions.json")

    def _load(self) -> None:
        path = self._grants_path()
        try:
            if os.path.isfile(path):
                with open(path) as f:
                    data: dict[str, Any] = json.load(f)
                for plugin_id, perms in data.items():
                    self._grants[plugin_id] = set(perms)
            logger.info("Plugin permissions loaded from %s", path)
        except Exception as e:
            logger.warning("Failed to load permissions: %s", e)

    def _save(self) -> None:
        path = self._grants_path()
        try:
            data = {pid: list(perms) for pid, perms in self._grants.items()}
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save permissions: %s", e)

    def grant(self, plugin_id: str, permission: str) -> None:
        if permission not in PERMISSION_GROUPS:
            logger.warning(
                "Unknown permission '%s' granted to '%s'", permission, plugin_id
            )
        if plugin_id not in self._grants:
            self._grants[plugin_id] = set()
        self._grants[plugin_id].add(permission)
        self._save()

    def revoke(self, plugin_id: str, permission: str) -> None:
        if plugin_id in self._grants:
            self._grants[plugin_id].discard(permission)
            self._save()

    def revoke_all(self, plugin_id: str) -> None:
        self._grants.pop(plugin_id, None)
        self._save()

    def check(self, plugin_id: str, permission: str) -> bool:
        return permission in self._grants.get(plugin_id, set())

    def check_any(self, plugin_id: str, permissions: list[str]) -> bool:
        granted = self._grants.get(plugin_id, set())
        return any(p in granted for p in permissions)

    def check_all(self, plugin_id: str, permissions: list[str]) -> bool:
        granted = self._grants.get(plugin_id, set())
        return all(p in granted for p in permissions)

    def get_granted(self, plugin_id: str) -> list[str]:
        return sorted(self._grants.get(plugin_id, set()))

    def get_required(self, plugin_id: str, requestd: list[str]) -> list[str]:
        granted = self._grants.get(plugin_id, set())
        return [p for p in requestd if p not in granted]

    def describe(self, permission: str) -> str:
        return PERMISSION_GROUPS.get(permission, f"Unknown permission: {permission}")

    def list_all(self) -> dict[str, str]:
        return dict(PERMISSION_GROUPS)
