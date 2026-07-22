from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shellsense.utils.config import ConfigManager
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

PRIVACY_DEFAULT_SETTINGS: dict[str, bool] = {
    "share_current_command": True,
    "share_command_args": True,
    "share_current_directory": True,
    "share_shell": True,
    "share_operating_system": True,
    "share_distribution": True,
    "share_kernel_version": True,
    "share_user": False,
    "share_hostname": False,
    "share_system_time": False,
    "share_git_repository": False,
    "share_git_branch": False,
    "share_git_status": False,
    "share_history": False,
    "share_environment_variables": False,
    "share_virtual_env": False,
    "share_container_info": False,
    "share_package_managers": False,
    "share_processes": False,
    "share_filesystems": False,
    "share_last_error": True,
    "share_last_command": True,
    "share_working_directory": True,
}


@dataclass
class PrivacySettings:
    settings: dict[str, bool] = field(
        default_factory=lambda: dict(PRIVACY_DEFAULT_SETTINGS)
    )

    def is_allowed(self, key: str) -> bool:
        return self.settings.get(key, False)

    def allow(self, key: str) -> None:
        self.settings[key] = True

    def deny(self, key: str) -> None:
        self.settings[key] = False

    def toggle(self, key: str) -> bool:
        current = self.settings.get(key, False)
        self.settings[key] = not current
        return self.settings[key]

    def to_dict(self) -> dict[str, bool]:
        return dict(self.settings)

    @classmethod
    def from_dict(cls, data: dict[str, bool]) -> PrivacySettings:
        merged = dict(PRIVACY_DEFAULT_SETTINGS)
        merged.update(data)
        return cls(settings=merged)

    def get_denied_keys(self) -> list[str]:
        return [k for k, v in self.settings.items() if not v]

    def get_allowed_keys(self) -> list[str]:
        return [k for k, v in self.settings.items() if v]


class PrivacyEngine:
    def __init__(self) -> None:
        self._settings = self._load_settings()

    def _load_settings(self) -> PrivacySettings:
        try:
            config = ConfigManager()
            stored = config.get("privacy", {})
            if isinstance(stored, dict):
                return PrivacySettings.from_dict(stored)
        except Exception as e:
            logger.debug("Failed to load privacy settings: %s", e)
        return PrivacySettings()

    def _save_settings(self) -> None:
        try:
            config = ConfigManager()
            config.set("privacy", self._settings.to_dict())
        except Exception as e:
            logger.debug("Failed to save privacy settings: %s", e)

    @property
    def settings(self) -> PrivacySettings:
        return self._settings

    def is_allowed(self, context_key: str) -> bool:
        setting_key = f"share_{context_key}"
        return self._settings.is_allowed(setting_key)

    def allow(self, context_key: str) -> None:
        setting_key = f"share_{context_key}"
        self._settings.allow(setting_key)
        self._save_settings()
        logger.info("Privacy: allowed %s", context_key)

    def deny(self, context_key: str) -> None:
        setting_key = f"share_{context_key}"
        self._settings.deny(setting_key)
        self._save_settings()
        logger.info("Privacy: denied %s", context_key)

    def toggle(self, context_key: str) -> bool:
        setting_key = f"share_{context_key}"
        result = self._settings.toggle(setting_key)
        self._save_settings()
        logger.info("Privacy: toggled %s to %s", context_key, result)
        return result

    def filter_context(self, context_dict: dict[str, Any]) -> dict[str, Any]:
        filtered: dict[str, Any] = {}
        for key, value in context_dict.items():
            if key == "env_vars" and isinstance(value, dict):
                if self.is_allowed("environment_variables"):
                    filtered[key] = value
                else:
                    filtered[key] = {}
            elif key == "recent_history" and isinstance(value, list):
                if self.is_allowed("history"):
                    filtered[key] = value
                else:
                    filtered[key] = []
            elif self.is_allowed(key):
                filtered[key] = value
        return filtered

    def reset_to_defaults(self) -> None:
        self._settings = PrivacySettings()
        self._save_settings()
        logger.info("Privacy: reset to defaults")

    def get_summary(self) -> dict[str, bool]:
        return self._settings.to_dict()

    def get_allowed_context_summary(self) -> str:
        allowed = self._settings.get_allowed_keys()
        return ", ".join(a.replace("share_", "") for a in allowed)
