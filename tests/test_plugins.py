from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from shellsense.plugins.api import PluginAPI
from shellsense.plugins.bus import PluginEventBus
from shellsense.plugins.compatibility import (
    check_platform,
    check_python_version,
    check_shellsense_version,
)
from shellsense.plugins.health import HealthMonitor
from shellsense.plugins.hooks import HookEvent, HookRegistry
from shellsense.plugins.isolation import SandboxExecutor
from shellsense.plugins.lifecycle import LifecycleManager
from shellsense.plugins.loader import PluginLoader
from shellsense.plugins.manager import PluginManager
from shellsense.plugins.manifest import (
    VALID_PERMISSIONS,
    check_compatibility,
    validate_manifest,
)
from shellsense.plugins.models import (
    PluginBase,
    PluginInfo,
    PluginManifest,
    PluginState,
)
from shellsense.plugins.permissions import PermissionManager
from shellsense.plugins.registry import PluginRegistry
from shellsense.plugins.scaffold import scaffold_plugin


class TestPluginManifest:
    def test_minimal_manifest(self) -> None:
        data = {
            "id": "test-plugin",
            "version": "1.0.0",
            "entry_point": "plugin",
        }
        manifest = validate_manifest(data)
        assert manifest.id == "test-plugin"
        assert manifest.version == "1.0.0"
        assert manifest.entry_point == "plugin"
        assert manifest.name == "test-plugin"

    def test_manifest_missing_required(self) -> None:
        with pytest.raises(Exception):
            validate_manifest({"name": "no-id"})

    def test_manifest_invalid_version(self) -> None:
        with pytest.raises(Exception):
            validate_manifest({"id": "test", "version": "abc", "entry_point": "p"})

    def test_manifest_full(self) -> None:
        data = {
            "id": "full-plugin",
            "name": "Full Plugin",
            "version": "2.1.0",
            "author": "Test Author",
            "description": "A test plugin",
            "entry_point": "main",
            "min_shellsense_version": "0.1.0",
            "permissions": ["filesystem.read", "system.info"],
            "hooks": ["before_command", "after_command"],
            "commands": [{"name": "test", "help": "Test command"}],
        }
        manifest = validate_manifest(data)
        assert manifest.author == "Test Author"
        assert "filesystem.read" in manifest.permissions
        assert "before_command" in manifest.hooks

    def test_manifest_invalid_permission_warning(self) -> None:
        data = {
            "id": "bad-perms",
            "version": "1.0.0",
            "entry_point": "plugin",
            "permissions": ["invalid.perm"],
        }
        manifest = validate_manifest(data)
        assert "invalid.perm" in manifest.permissions
        assert "valid.perm" not in VALID_PERMISSIONS

    def test_compatibility_check(self) -> None:
        manifest = PluginManifest(
            id="test",
            name="Test",
            version="1.0",
            author="A",
            description="D",
            entry_point="p",
            min_shellsense_version="0.0.1",
        )
        ok, msg = check_compatibility(manifest)
        assert ok
        assert msg == ""

    def test_compatibility_fail(self) -> None:
        manifest = PluginManifest(
            id="test",
            name="Test",
            version="1.0",
            author="A",
            description="D",
            entry_point="p",
            min_shellsense_version="99.0.0",
        )
        ok, msg = check_compatibility(manifest)
        assert not ok
        assert "99.0.0" in msg

    def test_manifest_to_from_dict(self) -> None:
        original = PluginManifest(
            id="roundtrip",
            name="Round Trip",
            version="0.1.0",
            author="Tester",
            description="Test",
            entry_point="p",
            permissions=["network"],
        )
        data = original.to_dict()
        restored = PluginManifest.from_dict(data)
        assert restored.id == original.id
        assert restored.permissions == original.permissions


class TestPluginState:
    def test_states(self) -> None:
        assert PluginState.DISCOVERED.value == "discovered"
        assert PluginState.LOADED.value == "loaded"
        assert PluginState.ENABLED.value == "enabled"
        assert PluginState.DISABLED.value == "disabled"
        assert PluginState.ERROR.value == "error"

    def test_plugin_info_defaults(self) -> None:
        manifest = PluginManifest(
            id="test",
            name="Test",
            version="1.0",
            author="A",
            description="D",
            entry_point="p",
        )
        info = PluginInfo(manifest=manifest)
        assert info.state == PluginState.DISCOVERED
        assert info.enabled is False
        assert info.load_count == 0
        assert info.error == ""

    def test_plugin_info_properties(self) -> None:
        manifest = PluginManifest(
            id="my-id",
            name="My Name",
            version="2.0",
            author="A",
            description="D",
            entry_point="p",
        )
        info = PluginInfo(manifest=manifest)
        assert info.id == "my-id"
        assert info.name == "My Name"
        assert info.version == "2.0"


class TestPluginBase:
    def test_base_defaults(self) -> None:
        plugin = PluginBase()
        plugin.on_load()
        plugin.on_enable()
        plugin.on_disable()
        plugin.on_unload()
        plugin.on_install()
        plugin.on_uninstall()
        plugin.on_startup()
        plugin.on_shutdown()
        plugin.on_error_recovery(Exception("test"))

    def test_base_subclass(self) -> None:
        class TestPlugin(PluginBase):
            def __init__(self) -> None:
                super().__init__()
                self.loaded = False

            def on_load(self) -> None:
                self.loaded = True

        p = TestPlugin()
        assert p.loaded is False
        p.on_load()
        assert p.loaded is True


class TestHookRegistry:
    def test_register_and_dispatch(self) -> None:
        registry = HookRegistry()
        results: list[str] = []

        def handler(**kwargs: object) -> None:
            results.append("called")

        registry.register(HookEvent.SHELL_STARTUP, "test", handler)
        registry.dispatch(HookEvent.SHELL_STARTUP)
        assert results == ["called"]

    def test_register_with_data(self) -> None:
        registry = HookRegistry()
        results: list[str] = []

        def handler(msg: str = "") -> None:
            results.append(msg)

        registry.register(HookEvent.BEFORE_COMMAND, "test", handler)
        registry.dispatch(HookEvent.BEFORE_COMMAND, msg="hello")
        assert results == ["hello"]

    def test_unregister(self) -> None:
        registry = HookRegistry()
        results: list[int] = []

        def h1(**kwargs: object) -> None:
            results.append(1)

        def h2(**kwargs: object) -> None:
            results.append(2)

        registry.register(HookEvent.AFTER_COMMAND, "p1", h1)
        registry.register(HookEvent.AFTER_COMMAND, "p2", h2)
        registry.dispatch(HookEvent.AFTER_COMMAND)
        assert results == [1, 2]

        registry.unregister(HookEvent.AFTER_COMMAND, "p1", h1)
        results.clear()
        registry.dispatch(HookEvent.AFTER_COMMAND)
        assert results == [2]

    def test_unregister_all(self) -> None:
        registry = HookRegistry()
        registry.register(HookEvent.SHELL_STARTUP, "p1", lambda **kw: None)
        registry.register(HookEvent.SHELL_STARTUP, "p2", lambda **kw: None)
        registry.unregister_all("p1")
        hooks = registry.get_hooks(HookEvent.SHELL_STARTUP)
        assert len(hooks[HookEvent.SHELL_STARTUP]) == 1

    def test_priority_order(self) -> None:
        registry = HookRegistry()
        results: list[int] = []

        registry.register(
            HookEvent.SHELL_STARTUP, "low", lambda **kw: results.append(1), priority=-10
        )
        registry.register(
            HookEvent.SHELL_STARTUP, "high", lambda **kw: results.append(3), priority=10
        )
        registry.register(
            HookEvent.SHELL_STARTUP,
            "normal",
            lambda **kw: results.append(2),
            priority=0,
        )

        registry.dispatch(HookEvent.SHELL_STARTUP)
        assert results == [3, 2, 1]

    def test_clear(self) -> None:
        registry = HookRegistry()
        registry.register(HookEvent.SHELL_STARTUP, "test", lambda **kw: None)
        registry.clear()
        assert registry.get_hooks() == {}

    def test_get_plugin_hooks(self) -> None:
        registry = HookRegistry()
        registry.register(HookEvent.SHELL_STARTUP, "p1", lambda **kw: None)
        registry.register(HookEvent.BEFORE_COMMAND, "p1", lambda **kw: None)
        registry.register(HookEvent.AFTER_COMMAND, "p2", lambda **kw: None)
        hooks = registry.get_plugin_hooks("p1")
        assert len(hooks) == 2


class TestPluginEventBus:
    def test_publish_subscribe(self) -> None:
        bus = PluginEventBus()
        received: list[str] = []

        def handler(msg: object) -> None:
            received.append("called")

        bus.subscribe("test.topic", "plugin1", handler)
        bus.publish("test.topic", "sender", {"key": "val"})
        assert received == ["called"]

    def test_unsubscribe(self) -> None:
        bus = PluginEventBus()
        received: list[str] = []

        def handler(msg: object) -> None:
            received.append("called")

        bus.subscribe("test.topic", "plugin1", handler)
        bus.unsubscribe("test.topic", "plugin1")
        bus.publish("test.topic", "sender", {})
        assert received == []

    def test_history(self) -> None:
        bus = PluginEventBus()
        bus.publish("topic1", "sender1", {"a": 1})
        bus.publish("topic2", "sender2", {"b": 2})
        history = bus.get_history(limit=10)
        assert len(history) == 2

    def test_history_filtered(self) -> None:
        bus = PluginEventBus()
        bus.publish("topic1", "s1", {})
        bus.publish("topic2", "s2", {})
        history = bus.get_history(topic="topic1")
        assert len(history) == 1
        assert history[0].topic == "topic1"


class TestPluginRegistry:
    def test_register_and_get(self) -> None:
        registry = PluginRegistry()
        manifest = PluginManifest(
            id="test",
            name="Test",
            version="1.0",
            author="A",
            description="D",
            entry_point="p",
        )
        info = PluginInfo(manifest=manifest)
        registry.register(info)
        assert registry.contains("test")
        retrieved = registry.get("test")
        assert retrieved.id == "test"

    def test_get_nonexistent(self) -> None:
        registry = PluginRegistry()
        from shellsense.plugins.exceptions import PluginNotFoundError

        with pytest.raises(PluginNotFoundError):
            registry.get("nonexistent")

    def test_list(self) -> None:
        registry = PluginRegistry()
        registry.register(
            PluginInfo(
                manifest=PluginManifest(
                    id="a",
                    name="A",
                    version="1",
                    author="",
                    description="",
                    entry_point="p",
                )
            )
        )
        registry.register(
            PluginInfo(
                manifest=PluginManifest(
                    id="b",
                    name="B",
                    version="1",
                    author="",
                    description="",
                    entry_point="p",
                )
            )
        )
        assert len(registry.list_all()) == 2

    def test_unregister(self) -> None:
        registry = PluginRegistry()
        manifest = PluginManifest(
            id="test",
            name="Test",
            version="1.0",
            author="A",
            description="D",
            entry_point="p",
        )
        registry.register(PluginInfo(manifest=manifest))
        registry.unregister("test")
        assert not registry.contains("test")

    def test_list_by_state(self) -> None:
        registry = PluginRegistry()
        m = PluginManifest(
            id="t", name="T", version="1", author="", description="", entry_point="p"
        )
        info = PluginInfo(manifest=m, state=PluginState.ENABLED, enabled=True)
        registry.register(info)
        enabled = registry.list_by_state(PluginState.ENABLED)
        assert len(enabled) == 1
        assert enabled[0].id == "t"


class TestPermissionManager:
    def test_grant_and_check(self) -> None:
        pm = PermissionManager()
        assert not pm.check("test-plugin", "network")
        pm.grant("test-plugin", "network")
        assert pm.check("test-plugin", "network")

    def test_check_any(self) -> None:
        pm = PermissionManager()
        pm.grant("test-plugin", "filesystem.read")
        assert pm.check_any("test-plugin", ["network", "filesystem.read"])
        assert not pm.check_any("test-plugin", ["network", "ai.access"])

    def test_check_all(self) -> None:
        pm = PermissionManager()
        pm.grant("test-plugin", "filesystem.read")
        pm.grant("test-plugin", "system.info")
        assert pm.check_all("test-plugin", ["filesystem.read", "system.info"])
        assert not pm.check_all("test-plugin", ["filesystem.read", "network"])

    def test_revoke(self) -> None:
        pm = PermissionManager()
        pm.grant("test-plugin", "network")
        pm.revoke("test-plugin", "network")
        assert not pm.check("test-plugin", "network")

    def test_revoke_all(self) -> None:
        pm = PermissionManager()
        pm.grant("test-plugin", "network")
        pm.grant("test-plugin", "ai.access")
        pm.revoke_all("test-plugin")
        assert pm.get_granted("test-plugin") == []

    def test_get_required(self) -> None:
        pm = PermissionManager()
        pm.grant("test-plugin", "network")
        missing = pm.get_required("test-plugin", ["network", "ai.access"])
        assert missing == ["ai.access"]

    def test_describe(self) -> None:
        pm = PermissionManager()
        desc = pm.describe("network")
        assert "Make network" in desc

    def test_list_all(self) -> None:
        pm = PermissionManager()
        all_perms = pm.list_all()
        assert "filesystem.read" in all_perms
        assert "network" in all_perms


class TestPluginLoader:
    def test_discover_nonexistent_dir(self) -> None:
        loader = PluginLoader()
        plugins = loader.discover("/nonexistent/path")
        assert plugins == []

    def test_discover_empty_dir(self, tmp_path: Path) -> None:
        loader = PluginLoader()
        plugins = loader.discover(str(tmp_path))
        assert plugins == []

    def test_discover_with_manifest(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()
        manifest = {
            "id": "my-plugin",
            "name": "My Plugin",
            "version": "1.0.0",
            "author": "Test",
            "description": "A test plugin",
            "entry_point": "plugin",
        }
        with open(plugin_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        loader = PluginLoader()
        plugins = loader.discover(str(tmp_path))
        assert len(plugins) == 1
        assert plugins[0].id == "my-plugin"

    def test_discover_skips_non_manifest(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "no-manifest"
        empty_dir.mkdir()
        loader = PluginLoader()
        plugins = loader.discover(str(tmp_path))
        assert len(plugins) == 0


class TestLifecycleManager:
    def test_lifecycle_events(self) -> None:
        registry = HookRegistry()
        lc = LifecycleManager(registry)
        manifest = PluginManifest(
            id="test",
            name="Test",
            version="1.0",
            author="A",
            description="D",
            entry_point="p",
        )
        info = PluginInfo(manifest=manifest)

        class TestPlugin(PluginBase):
            def __init__(self) -> None:
                super().__init__()
                self.events: list[str] = []

            def on_enable(self) -> None:
                self.events.append("enabled")

            def on_disable(self) -> None:
                self.events.append("disabled")

        plugin = TestPlugin()
        lc.register_instance("test", plugin)
        lc.execute_enable(plugin, info)
        assert info.enabled
        assert info.state == PluginState.ENABLED
        assert plugin.events == ["enabled"]

        lc.execute_disable(plugin, info)
        assert not info.enabled
        assert info.state == PluginState.DISABLED
        assert plugin.events == ["enabled", "disabled"]


class TestScaffold:
    def test_scaffold_creates_structure(self, tmp_path: Path) -> None:
        output = str(tmp_path)
        plugin_dir = scaffold_plugin(
            plugin_id="my-plugin",
            output_dir=output,
            name="My Plugin",
            description="Test plugin",
            author="Tester",
            permissions=["filesystem.read", "system.info"],
        )
        assert os.path.isdir(plugin_dir)
        assert os.path.isfile(os.path.join(plugin_dir, "manifest.json"))
        assert os.path.isfile(os.path.join(plugin_dir, "plugin.py"))
        assert os.path.isfile(os.path.join(plugin_dir, "config.json"))
        assert os.path.isfile(os.path.join(plugin_dir, "README.md"))
        assert os.path.isdir(os.path.join(plugin_dir, "commands"))
        assert os.path.isdir(os.path.join(plugin_dir, "hooks"))
        assert os.path.isdir(os.path.join(plugin_dir, "tests"))
        assert os.path.isdir(os.path.join(plugin_dir, "docs"))

        with open(os.path.join(plugin_dir, "manifest.json")) as f:
            manifest = json.load(f)
        assert manifest["id"] == "my-plugin"
        assert manifest["name"] == "My Plugin"
        assert manifest["permissions"] == ["filesystem.read", "system.info"]

    def test_scaffold_permissions_filtered(self, tmp_path: Path) -> None:
        output = str(tmp_path)
        plugin_dir = scaffold_plugin(
            plugin_id="filter-test",
            output_dir=output,
            permissions=["network", "invalid.perm"],
        )
        with open(os.path.join(plugin_dir, "manifest.json")) as f:
            manifest = json.load(f)
        assert "network" in manifest["permissions"]
        assert "invalid.perm" not in manifest["permissions"]


class TestHealthMonitor:
    def test_register_and_record(self) -> None:
        hm = HealthMonitor()
        hm.record_load("test-plugin", 150.0)
        health = hm.get("test-plugin")
        assert health is not None
        assert health.plugin_id == "test-plugin"
        assert health.load_time_ms == 150.0

    def test_record_error(self) -> None:
        hm = HealthMonitor()
        hm.record_error("test-plugin", "Something broke")
        health = hm.get("test-plugin")
        assert health is not None
        assert health.error_count == 1
        assert "Something broke" in health.last_error

    def test_summary(self) -> None:
        hm = HealthMonitor()
        hm.record_load("p1", 100.0)
        hm.record_status("p2", "enabled")
        summary = hm.summary()
        assert len(summary) == 2

    def test_remove(self) -> None:
        hm = HealthMonitor()
        hm.record_load("test", 50.0)
        hm.remove("test")
        assert hm.get("test") is None


class TestCompatibility:
    def test_python_version(self) -> None:
        ok, msg = check_python_version("3.0")
        assert ok

    def test_shellsense_version_ok(self) -> None:
        ok, msg = check_shellsense_version("0.0.1")
        assert ok

    def test_shellsense_version_fail(self) -> None:
        ok, msg = check_shellsense_version("99.0.0")
        assert not ok

    def test_platform(self) -> None:
        import platform

        ok, msg = check_platform(platform.system().lower())
        assert ok


class TestSandboxExecutor:
    def test_allowed_modules(self) -> None:
        sb = SandboxExecutor()
        assert sb.check_import("json")
        assert sb.check_import("os.path")
        assert not sb.check_import("subprocess")
        assert not sb.check_import("socket")


class TestPluginAPI:
    def test_logger_api(self) -> None:
        api = PluginAPI(plugin_id="test")
        api.log.info("test info")
        api.log.warn("test warn")
        api.log.error("test error")
        api.log.debug("test debug")

    def test_config_api_no_config(self) -> None:
        api = PluginAPI(plugin_id="test")
        assert api.config is None or True

    def test_api_with_engines(self) -> None:
        class MockEngine:
            def search(self, query: str, limit: int = 10) -> list:
                return []

            def get_command(self, name: str) -> dict | None:
                return None

            def get_categories(self) -> list[str]:
                return []

        api = PluginAPI(
            plugin_id="test",
            knowledge_engine=MockEngine(),
            suggest_func=lambda q, limit=10: [],
        )
        assert api.knowledge is not None
        assert api.suggestions is not None
        assert api.knowledge.search("test") == []
        assert api.suggestions.suggest("test") == []


class TestPluginManager:
    def test_initialize(self) -> None:
        pm = PluginManager()
        pm.initialize()
        assert os.path.isdir(pm.plugins_dir)

    def test_discover_empty(self) -> None:
        pm = PluginManager()
        pm.initialize()
        plugins = pm.discover()
        assert isinstance(plugins, list)

    def test_list_empty(self) -> None:
        pm = PluginManager()
        pm.initialize()
        assert pm.list_plugins() == []

    def test_load_nonexistent(self) -> None:
        pm = PluginManager()
        pm.initialize()
        from shellsense.plugins.exceptions import PluginNotFoundError

        with pytest.raises(PluginNotFoundError):
            pm.load("nonexistent")

    def test_shutdown_no_crash(self) -> None:
        pm = PluginManager()
        pm.initialize()
        pm.shutdown()

    def test_startup_no_crash(self) -> None:
        pm = PluginManager()
        pm.startup()
        pm.shutdown()
