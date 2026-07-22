from __future__ import annotations

import json
import os
from typing import Any

from shellsense import __version__
from shellsense.plugins.exceptions import PluginLoadError
from shellsense.plugins.models import PluginManifest
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

REQUIRED_MANIFEST_FIELDS = {"id", "version", "entry_point"}
OPTIONAL_MANIFEST_FIELDS = {
    "name",
    "author",
    "description",
    "min_shellsense_version",
    "max_shellsense_version",
    "dependencies",
    "permissions",
    "hooks",
    "commands",
    "config_schema",
    "platforms",
    "shells",
    "license",
    "homepage",
    "tags",
}
VALID_PERMISSIONS = {
    "filesystem.read",
    "filesystem.write",
    "network",
    "ai.access",
    "shell.history",
    "env.variables",
    "system.info",
    "git.access",
    "logs.access",
    "automation.generate",
    "template.manage",
    "shell.execute",
    "process.list",
    "package.manage",
}


def load_manifest(plugin_dir: str) -> PluginManifest:
    manifest_path = os.path.join(plugin_dir, "manifest.json")
    if not os.path.isfile(manifest_path):
        raise PluginLoadError(
            os.path.basename(plugin_dir),
            f"manifest.json not found in {plugin_dir}",
        )
    try:
        with open(manifest_path) as f:
            data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        raise PluginLoadError(
            os.path.basename(plugin_dir), f"invalid manifest.json: {e}"
        )

    return validate_manifest(data, plugin_dir)


def validate_manifest(data: dict[str, Any], plugin_dir: str = "") -> PluginManifest:
    missing = REQUIRED_MANIFEST_FIELDS - set(data.keys())
    if missing:
        raise PluginLoadError(
            data.get("id", "unknown"),
            f"missing required fields: {', '.join(sorted(missing))}",
        )

    plugin_id = data["id"]
    unknown = set(data.keys()) - REQUIRED_MANIFEST_FIELDS - OPTIONAL_MANIFEST_FIELDS
    if unknown:
        logger.warning(
            "Plugin '%s' has unknown manifest fields: %s", plugin_id, unknown
        )

    if not isinstance(data["id"], str) or not data["id"].strip():
        raise PluginLoadError(plugin_id, "id must be a non-empty string")

    if not isinstance(data["version"], str) or not _is_valid_version(data["version"]):
        raise PluginLoadError(plugin_id, f"invalid version format: {data['version']}")

    if not isinstance(data.get("entry_point", ""), str) or not data["entry_point"]:
        raise PluginLoadError(plugin_id, "entry_point must be a non-empty string")

    invalid_perms = set(data.get("permissions", [])) - VALID_PERMISSIONS
    if invalid_perms:
        logger.warning(
            "Plugin '%s' declares unknown permissions: %s",
            plugin_id,
            invalid_perms,
        )

    if not _is_valid_entry_point(data["entry_point"]):
        logger.warning(
            "Plugin '%s' entry_point '%s' may be invalid",
            plugin_id,
            data["entry_point"],
        )

    return PluginManifest.from_dict(data)


def _is_valid_version(version: str) -> bool:
    parts = version.split(".")
    if len(parts) < 2 or len(parts) > 4:
        return False
    return all(p.isdigit() or (p.startswith("rc") and p[2:].isdigit()) for p in parts)


def _is_valid_entry_point(entry_point: str) -> bool:
    parts = entry_point.split(".")
    if not parts:
        return False
    return all(p.isidentifier() for p in parts)


def check_compatibility(manifest: PluginManifest) -> tuple[bool, str]:
    current = __version__
    min_v = manifest.min_shellsense_version
    max_v = manifest.max_shellsense_version

    if min_v and _compare_versions(current, min_v) < 0:
        return False, (f"Plugin requires ShellSense >= {min_v}, current is {current}")

    if max_v and _compare_versions(current, max_v) > 0:
        return False, (f"Plugin requires ShellSense <= {max_v}, current is {current}")

    return True, ""


def _compare_versions(v1: str, v2: str) -> int:
    parts1 = [int(p) for p in v1.split(".") if p.isdigit()]
    parts2 = [int(p) for p in v2.split(".") if p.isdigit()]
    for a, b in zip(parts1, parts2):
        if a < b:
            return -1
        if a > b:
            return 1
    if len(parts1) < len(parts2):
        return -1
    if len(parts1) > len(parts2):
        return 1
    return 0
