from __future__ import annotations

from shellsense.plugins.exceptions import PluginNotFoundError
from shellsense.plugins.models import PluginInfo, PluginState


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginInfo] = {}

    def register(self, info: PluginInfo) -> None:
        self._plugins[info.id] = info

    def unregister(self, plugin_id: str) -> None:
        self._plugins.pop(plugin_id, None)

    def get(self, plugin_id: str) -> PluginInfo:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise PluginNotFoundError(plugin_id)
        return plugin

    def get_or_none(self, plugin_id: str) -> PluginInfo | None:
        return self._plugins.get(plugin_id)

    def list_all(self) -> list[PluginInfo]:
        return list(self._plugins.values())

    def list_by_state(self, state: PluginState) -> list[PluginInfo]:
        return [p for p in self._plugins.values() if p.state == state]

    def list_enabled(self) -> list[PluginInfo]:
        return [p for p in self._plugins.values() if p.enabled]

    def update_state(self, plugin_id: str, state: PluginState) -> None:
        if plugin_id in self._plugins:
            self._plugins[plugin_id].state = state

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        if plugin_id in self._plugins:
            self._plugins[plugin_id].enabled = enabled

    def set_error(self, plugin_id: str, error: str) -> None:
        if plugin_id in self._plugins:
            self._plugins[plugin_id].error = error
            self._plugins[plugin_id].state = PluginState.ERROR

    def contains(self, plugin_id: str) -> bool:
        return plugin_id in self._plugins

    def count(self) -> int:
        return len(self._plugins)

    def clear(self) -> None:
        self._plugins.clear()
