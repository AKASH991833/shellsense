from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PluginHealth:
    plugin_id: str
    status: str = "unknown"
    last_check: float = 0.0
    load_time_ms: float = 0.0
    error_count: int = 0
    last_error: str = ""
    memory_estimate_kb: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    def __init__(self) -> None:
        self._health: dict[str, PluginHealth] = {}

    def register(self, plugin_id: str) -> None:
        if plugin_id not in self._health:
            self._health[plugin_id] = PluginHealth(plugin_id=plugin_id)

    def record_load(self, plugin_id: str, load_time_ms: float) -> None:
        self.register(plugin_id)
        self._health[plugin_id].load_time_ms = load_time_ms
        self._health[plugin_id].status = "loaded"
        self._health[plugin_id].last_check = time.time()

    def record_error(self, plugin_id: str, error: str) -> None:
        self.register(plugin_id)
        h = self._health[plugin_id]
        h.error_count += 1
        h.last_error = error
        h.status = "error"
        h.last_check = time.time()
        logger.warning("Plugin '%s' error (#%d): %s", plugin_id, h.error_count, error)

    def record_status(self, plugin_id: str, status: str) -> None:
        self.register(plugin_id)
        self._health[plugin_id].status = status
        self._health[plugin_id].last_check = time.time()

    def get(self, plugin_id: str) -> PluginHealth | None:
        return self._health.get(plugin_id)

    def get_all(self) -> dict[str, PluginHealth]:
        return dict(self._health)

    def remove(self, plugin_id: str) -> None:
        self._health.pop(plugin_id, None)

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "plugin_id": h.plugin_id,
                "status": h.status,
                "error_count": h.error_count,
                "last_error": h.last_error,
                "last_check": h.last_check,
            }
            for h in self._health.values()
        ]
