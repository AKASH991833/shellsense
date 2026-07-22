from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any

from shellsense.marketplace.models import AuditEntry
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_shellsense_dir

logger = get_logger(__name__)


class EnterprisePolicies:
    def __init__(self, config_manager: Any = None, data_dir: str | None = None) -> None:
        self._config = config_manager
        self._data_dir = data_dir
        self._approved: list[str] = []
        self._blocked: list[str] = []
        self._mandatory: list[str] = []
        self._audit_log: list[AuditEntry] = []
        if data_dir is None:
            self._load()

    def _policies_path(self) -> str:
        if self._data_dir:
            return os.path.join(self._data_dir, "enterprise.json")
        return os.path.join(get_shellsense_dir(), "marketplace", "enterprise.json")

    def _load(self) -> None:
        path = self._policies_path()
        try:
            if os.path.isfile(path):
                with open(path) as f:
                    data: dict[str, Any] = json.load(f)
                self._approved = data.get("approved", [])
                self._blocked = data.get("blocked", [])
                self._mandatory = data.get("mandatory", [])
                audit_data = data.get("audit_log", [])
                self._audit_log = [AuditEntry(**a) for a in audit_data]
            else:
                self._load_from_config()
        except Exception as e:
            logger.warning("Failed to load enterprise policies: %s", e)
            self._load_from_config()

    def _load_from_config(self) -> None:
        if self._config:
            self._approved = self._config.get("enterprise.approved_plugins", [])
            self._blocked = self._config.get("enterprise.blocked_plugins", [])
            self._mandatory = self._config.get("enterprise.mandatory_plugins", [])

    def _save(self) -> None:
        path = self._policies_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(
                    {
                        "approved": self._approved,
                        "blocked": self._blocked,
                        "mandatory": self._mandatory,
                        "audit_log": [a.__dict__ for a in self._audit_log],
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error("Failed to save enterprise policies: %s", e)

    def check_install_policy(self, plugin_id: str) -> dict[str, Any]:
        if plugin_id in self._blocked:
            return {"allowed": False, "reason": f"Plugin '{plugin_id}' is blocked"}
        if self._approved and plugin_id not in self._approved:
            return {
                "allowed": False,
                "reason": f"Plugin '{plugin_id}' is not in approved list",
            }
        return {"allowed": True, "reason": ""}

    def approve_plugin(self, plugin_id: str) -> None:
        if plugin_id not in self._approved:
            self._approved.append(plugin_id)
            self._save()
            self._audit("approve", plugin_id, "", "Plugin approved")

    def block_plugin(self, plugin_id: str, reason: str = "") -> None:
        if plugin_id not in self._blocked:
            self._blocked.append(plugin_id)
            self._approved = [p for p in self._approved if p != plugin_id]
            self._save()
            self._audit("block", plugin_id, "", f"Plugin blocked: {reason}")

    def set_mandatory(self, plugin_id: str) -> None:
        if plugin_id not in self._mandatory:
            self._mandatory.append(plugin_id)
            self._save()

    def remove_mandatory(self, plugin_id: str) -> None:
        self._mandatory = [p for p in self._mandatory if p != plugin_id]
        self._save()

    def get_approved(self) -> list[str]:
        return list(self._approved)

    def get_blocked(self) -> list[str]:
        return list(self._blocked)

    def get_mandatory(self) -> list[str]:
        return list(self._mandatory)

    def _audit(
        self,
        action: str,
        plugin_id: str,
        version: str,
        details: str = "",
        success: bool = True,
    ) -> None:
        entry = AuditEntry(
            action=action,
            plugin_id=plugin_id,
            version=version,
            user=os.environ.get("USER", "unknown"),
            timestamp=datetime.now(UTC).isoformat(),
            details=details,
            success=success,
        )
        self._audit_log.append(entry)
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]

    def get_audit_log(self, limit: int = 100) -> list[AuditEntry]:
        return self._audit_log[-limit:]

    def get_compliance_report(self) -> dict[str, Any]:
        return {
            "approved_count": len(self._approved),
            "blocked_count": len(self._blocked),
            "mandatory_count": len(self._mandatory),
            "total_audit_entries": len(self._audit_log),
            "recent_audit_entries": self._audit_log[-10:],
        }

    def is_approved(self, plugin_id: str) -> bool:
        return plugin_id in self._approved

    def is_blocked(self, plugin_id: str) -> bool:
        return plugin_id in self._blocked

    def is_mandatory(self, plugin_id: str) -> bool:
        return plugin_id in self._mandatory
