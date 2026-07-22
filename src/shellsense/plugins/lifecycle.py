from __future__ import annotations

from shellsense.plugins.exceptions import PluginError
from shellsense.plugins.hooks import HookEvent, HookRegistry
from shellsense.plugins.models import (
    PluginBase,
    PluginInfo,
    PluginState,
)
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class LifecycleManager:
    def __init__(self, hook_registry: HookRegistry) -> None:
        self._hooks = hook_registry
        self._instances: dict[str, PluginBase] = {}

    def get_instance(self, plugin_id: str) -> PluginBase | None:
        return self._instances.get(plugin_id)

    def get_all_instances(self) -> dict[str, PluginBase]:
        return dict(self._instances)

    def execute_install(self, plugin: PluginBase, info: PluginInfo) -> None:
        try:
            plugin.on_install()
            self._hooks.dispatch(HookEvent.PLUGIN_INSTALL, plugin_id=info.id)
            logger.info("Plugin '%s' installed", info.id)
        except Exception as e:
            raise PluginError(f"Plugin '{info.id}' install failed: {e}")

    def execute_enable(self, plugin: PluginBase, info: PluginInfo) -> None:
        try:
            info.state = PluginState.ENABLED
            info.enabled = True
            plugin.on_enable()
            self._hooks.dispatch(HookEvent.PLUGIN_ENABLE, plugin_id=info.id)
            logger.info("Plugin '%s' enabled", info.id)
        except Exception as e:
            info.state = PluginState.ERROR
            info.enabled = False
            raise PluginError(f"Plugin '{info.id}' enable failed: {e}")

    def execute_disable(self, plugin: PluginBase, info: PluginInfo) -> None:
        try:
            plugin.on_disable()
            info.state = PluginState.DISABLED
            info.enabled = False
            self._hooks.dispatch(HookEvent.PLUGIN_DISABLE, plugin_id=info.id)
            logger.info("Plugin '%s' disabled", info.id)
        except Exception as e:
            info.state = PluginState.ERROR
            raise PluginError(f"Plugin '{info.id}' disable failed: {e}")

    def execute_unload(self, plugin: PluginBase, info: PluginInfo) -> None:
        try:
            plugin.on_unload()
            self._hooks.unregister_all(info.id)
            info.state = PluginState.DISCOVERED
            info.enabled = False
            self._instances.pop(info.id, None)
            logger.info("Plugin '%s' unloaded", info.id)
        except Exception as e:
            raise PluginError(f"Plugin '{info.id}' unload failed: {e}")

    def execute_startup(self, plugin: PluginBase, info: PluginInfo) -> None:
        try:
            plugin.on_startup()
            logger.debug("Plugin '%s' startup complete", info.id)
        except Exception as e:
            logger.warning("Plugin '%s' startup hook failed: %s", info.id, e)

    def execute_shutdown(self, plugin: PluginBase, info: PluginInfo) -> None:
        try:
            plugin.on_shutdown()
            logger.debug("Plugin '%s' shutdown complete", info.id)
        except Exception as e:
            logger.warning("Plugin '%s' shutdown hook failed: %s", info.id, e)

    def execute_error_recovery(
        self, plugin: PluginBase, info: PluginInfo, error: Exception
    ) -> None:
        try:
            plugin.on_error_recovery(error)
            info.state = PluginState.LOADED
            logger.info("Plugin '%s' recovered from error", info.id)
        except Exception as e:
            logger.error("Plugin '%s' error recovery failed: %s", info.id, e)

    def register_instance(self, plugin_id: str, instance: PluginBase) -> None:
        self._instances[plugin_id] = instance
