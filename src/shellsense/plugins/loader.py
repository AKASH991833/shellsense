from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import time
from typing import Any

from shellsense.plugins.exceptions import PluginLoadError
from shellsense.plugins.manifest import load_manifest
from shellsense.plugins.models import (
    PluginBase,
    PluginInfo,
    PluginState,
)
from shellsense.utils.logging import get_logger

logger = get_logger(__name__)


class PluginLoader:
    def discover(self, plugins_dir: str) -> list[PluginInfo]:
        discovered: list[PluginInfo] = []
        if not os.path.isdir(plugins_dir):
            logger.info("Plugins directory does not exist: %s", plugins_dir)
            return discovered

        for entry in sorted(os.listdir(plugins_dir)):
            plugin_path = os.path.join(plugins_dir, entry)
            if not os.path.isdir(plugin_path):
                continue
            manifest_path = os.path.join(plugin_path, "manifest.json")
            if not os.path.isfile(manifest_path):
                continue
            try:
                manifest = load_manifest(plugin_path)
                info = PluginInfo(
                    manifest=manifest,
                    state=PluginState.DISCOVERED,
                    path=plugin_path,
                )
                discovered.append(info)
                logger.debug(
                    "Discovered plugin '%s' v%s", manifest.id, manifest.version
                )
            except Exception as e:
                logger.warning("Failed to discover plugin at %s: %s", plugin_path, e)

        return discovered

    def load(self, plugin_info: PluginInfo, api: Any = None) -> PluginBase:
        start = time.time()
        plugin_id = plugin_info.id
        manifest = plugin_info.manifest
        plugin_path = plugin_info.path

        if plugin_path not in sys.path:
            sys.path.insert(0, plugin_path)

        entry_point = manifest.entry_point
        try:
            mod = importlib.import_module(entry_point)
        except ImportError as e:
            raise PluginLoadError(
                plugin_id, f"cannot import entry point '{entry_point}': {e}"
            )

        plugin_class = self._find_plugin_class(mod, plugin_id)
        if plugin_class is None:
            raise PluginLoadError(
                plugin_id,
                f"no PluginBase subclass found in module '{entry_point}'",
            )

        try:
            instance: PluginBase = plugin_class()
            instance.manifest = manifest
            instance.config = plugin_info.config
            instance._api = api
            instance._logger = logger
            instance.on_load()
        except Exception as e:
            raise PluginLoadError(plugin_id, f"instantiation failed: {e}")

        elapsed = (time.time() - start) * 1000
        logger.info(
            "Loaded plugin '%s' v%s in %.0fms",
            plugin_id,
            manifest.version,
            elapsed,
        )
        return instance

    def _find_plugin_class(
        self, module: Any, plugin_id: str
    ) -> type[PluginBase] | None:
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, PluginBase)
                and obj is not PluginBase
            ):
                return obj
        return None
