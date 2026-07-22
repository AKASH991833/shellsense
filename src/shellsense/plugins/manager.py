from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from shellsense.plugins.api import PluginAPI
from shellsense.plugins.bus import PluginEventBus
from shellsense.plugins.exceptions import (
    PluginCompatibilityError,
    PluginDependencyError,
    PluginNotFoundError,
    PluginPermissionError,
)
from shellsense.plugins.health import HealthMonitor
from shellsense.plugins.hooks import HookEvent, HookRegistry
from shellsense.plugins.isolation import SandboxExecutor
from shellsense.plugins.lifecycle import LifecycleManager
from shellsense.plugins.loader import PluginLoader
from shellsense.plugins.manifest import check_compatibility
from shellsense.plugins.models import PluginBase, PluginInfo, PluginState
from shellsense.plugins.permissions import PermissionManager
from shellsense.plugins.registry import PluginRegistry
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_plugins_dir

logger = get_logger(__name__)


class PluginManager:
    def __init__(
        self,
        knowledge_engine: Any = None,
        suggest_func: Any = None,
        ai_engine: Any = None,
        context_collector: Any = None,
        automation_engine: Any = None,
        template_library: Any = None,
        config_manager: Any = None,
        shell_integration: Any = None,
        formatter: Any = None,
    ) -> None:
        self._plugins_dir = get_plugins_dir()
        self._knowledge_engine = knowledge_engine
        self._suggest_func = suggest_func
        self._ai_engine = ai_engine
        self._context_collector = context_collector
        self._automation_engine = automation_engine
        self._template_library = template_library
        self._config_manager = config_manager
        self._shell_integration = shell_integration
        self._formatter = formatter

        self.registry = PluginRegistry()
        self.loader = PluginLoader()
        self.hooks = HookRegistry()
        self.bus = PluginEventBus()
        self.permissions = PermissionManager()
        self.health = HealthMonitor()
        self.lifecycle = LifecycleManager(self.hooks)
        self.sandbox = SandboxExecutor()

        self._initialized = False

    @property
    def plugins_dir(self) -> Path:
        return self._plugins_dir

    def initialize(self) -> None:
        if self._initialized:
            return
        os.makedirs(str(self._plugins_dir), exist_ok=True)
        self._initialized = True
        logger.info("Plugin manager initialized (dir: %s)", self._plugins_dir)

    def discover(self) -> list[PluginInfo]:
        self.initialize()
        discovered = self.loader.discover(str(self._plugins_dir))
        for info in discovered:
            if not self.registry.contains(info.id):
                self.registry.register(info)
        return discovered

    def load(self, plugin_id: str) -> PluginBase:
        info = self.registry.get(plugin_id)
        if info.state in (PluginState.LOADED, PluginState.ENABLED):
            instance = self.lifecycle.get_instance(plugin_id)
            if instance:
                return instance

        self._check_dependencies(info)
        compatible, msg = check_compatibility(info.manifest)
        if not compatible:
            raise PluginCompatibilityError(plugin_id, info.version, msg)

        self._check_required_permissions(info)

        api = self._build_api(plugin_id)
        instance = self.loader.load(info, api=api)
        self.lifecycle.register_instance(plugin_id, instance)
        info.state = PluginState.LOADED
        info.load_count += 1
        info.last_loaded = time.time()
        self.health.record_load(plugin_id, 0.0)
        return instance

    def enable(self, plugin_id: str) -> None:
        info = self.registry.get(plugin_id)
        instance = self.lifecycle.get_instance(plugin_id)
        if instance is None:
            instance = self.load(plugin_id)
            info = self.registry.get(plugin_id)
        if info.enabled:
            logger.debug("Plugin '%s' already enabled", plugin_id)
            return
        self.lifecycle.execute_enable(instance, info)
        self.health.record_status(plugin_id, "enabled")

    def disable(self, plugin_id: str) -> None:
        info = self.registry.get(plugin_id)
        instance = self.lifecycle.get_instance(plugin_id)
        if instance and info.enabled:
            self.lifecycle.execute_disable(instance, info)
            self.health.record_status(plugin_id, "disabled")

    def unload(self, plugin_id: str) -> None:
        info = self.registry.get(plugin_id)
        if info.enabled:
            self.disable(plugin_id)
        instance = self.lifecycle.get_instance(plugin_id)
        if instance:
            self.lifecycle.execute_unload(instance, info)
            self.bus.unsubscribe_all(plugin_id)
            self.health.remove(plugin_id)
        self.registry.update_state(plugin_id, PluginState.DISCOVERED)

    def reload(self, plugin_id: str) -> None:
        was_enabled = self.registry.get(plugin_id).enabled
        self.unload(plugin_id)
        self.load(plugin_id)
        if was_enabled:
            self.enable(plugin_id)

    def install(self, plugin_path: str) -> PluginInfo:
        if not os.path.isdir(plugin_path):
            raise FileNotFoundError(f"Plugin directory not found: {plugin_path}")

        from shellsense.plugins.manifest import load_manifest

        manifest = load_manifest(plugin_path)
        plugin_id = manifest.id

        from shutil import copytree

        target_dir = os.path.join(self._plugins_dir, plugin_id)
        if os.path.exists(target_dir):
            raise FileExistsError(
                f"Plugin '{plugin_id}' already installed at {target_dir}"
            )

        copytree(plugin_path, target_dir)
        info = PluginInfo(
            manifest=manifest,
            state=PluginState.DISCOVERED,
            path=target_dir,
        )
        self.registry.register(info)
        logger.info("Installed plugin '%s' from %s", plugin_id, plugin_path)
        return info

    def remove(self, plugin_id: str) -> None:
        self.unload(plugin_id)
        info = self.registry.get(plugin_id)
        self.permissions.revoke_all(plugin_id)
        self.registry.unregister(plugin_id)

        import shutil

        if os.path.isdir(info.path):
            shutil.rmtree(info.path)
            logger.info("Removed plugin directory: %s", info.path)

        self.bus.publish("plugin.removed", "manager", {"plugin_id": plugin_id})
        logger.info("Removed plugin '%s'", plugin_id)

    def validate_plugin(self, plugin_id: str) -> list[str]:
        issues: list[str] = []
        try:
            info = self.registry.get(plugin_id)
        except PluginNotFoundError:
            return ["Plugin not found in registry"]

        manifest = info.manifest
        compatible, msg = check_compatibility(manifest)
        if not compatible:
            issues.append(msg)

        if not os.path.isdir(info.path):
            issues.append(f"Plugin directory missing: {info.path}")

        manifest_path = os.path.join(info.path, "manifest.json")
        if not os.path.isfile(manifest_path):
            issues.append("manifest.json not found")

        if not os.path.isfile(os.path.join(info.path, f"{manifest.entry_point}.py")):
            issues.append(f"Entry point '{manifest.entry_point}.py' not found")

        for dep_id in manifest.dependencies:
            if not self.registry.contains(dep_id):
                issues.append(f"Missing dependency: {dep_id}")

        missing_perms = self._get_missing_permissions(info)
        if missing_perms:
            issues.append(f"Missing permissions: {', '.join(missing_perms)}")

        return issues

    def get_plugin(self, plugin_id: str) -> PluginInfo:
        return self.registry.get(plugin_id)

    def get_instance(self, plugin_id: str) -> PluginBase | None:
        return self.lifecycle.get_instance(plugin_id)

    def list_plugins(self) -> list[PluginInfo]:
        return self.registry.list_all()

    def list_enabled(self) -> list[PluginInfo]:
        return self.registry.list_enabled()

    def get_health(self, plugin_id: str) -> Any:
        return self.health.get(plugin_id)

    def get_health_summary(self) -> list[dict[str, Any]]:
        return self.health.summary()

    def get_plugin_permissions(self, plugin_id: str) -> list[str]:
        return self.permissions.get_granted(plugin_id)

    def grant_permission(self, plugin_id: str, permission: str) -> None:
        self.permissions.grant(plugin_id, permission)

    def revoke_permission(self, plugin_id: str, permission: str) -> None:
        self.permissions.revoke(plugin_id, permission)

    def shutdown(self) -> None:
        for info in self.registry.list_enabled():
            instance = self.lifecycle.get_instance(info.id)
            if instance:
                self.lifecycle.execute_shutdown(instance, info)
        self.hooks.dispatch(HookEvent.SHELL_SHUTDOWN)
        self.bus.publish("system.shutdown", "manager", {})
        logger.info("Plugin manager shut down")

    def startup(self) -> None:
        self.initialize()
        self.discover()
        for info in self.list_plugins():
            try:
                self.load(info.id)
            except Exception as e:
                logger.warning("Could not load plugin '%s': %s", info.id, e)
        self.hooks.dispatch(HookEvent.SHELL_STARTUP)
        self.bus.publish("system.startup", "manager", {})
        logger.info(
            "Plugin manager startup complete (%d plugins)",
            self.registry.count(),
        )

    def _build_api(self, plugin_id: str) -> PluginAPI:
        return PluginAPI(
            plugin_id=plugin_id,
            knowledge_engine=self._knowledge_engine,
            suggest_func=self._suggest_func,
            ai_engine=self._ai_engine,
            context_collector=self._context_collector,
            automation_engine=self._automation_engine,
            template_library=self._template_library,
            config_manager=self._config_manager,
            shell_integration=self._shell_integration,
            formatter=self._formatter,
        )

    def _check_dependencies(self, info: PluginInfo) -> None:
        for dep_id, dep_version in info.manifest.dependencies.items():
            if not self.registry.contains(dep_id):
                raise PluginDependencyError(info.id, dep_id)
            dep_info = self.registry.get(dep_id)
            if dep_version and dep_info.version != dep_version:
                logger.warning(
                    "Plugin '%s' requires %s@%s, found %s@%s",
                    info.id,
                    dep_id,
                    dep_version,
                    dep_id,
                    dep_info.version,
                )

    def _check_required_permissions(self, info: PluginInfo) -> None:
        for perm in info.manifest.permissions:
            if not self.permissions.check(info.id, perm):
                raise PluginPermissionError(info.id, perm)

    def _get_missing_permissions(self, info: PluginInfo) -> list[str]:
        return [
            p
            for p in info.manifest.permissions
            if not self.permissions.check(info.id, p)
        ]
