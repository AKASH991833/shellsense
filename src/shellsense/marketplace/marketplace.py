from __future__ import annotations

import json
import os
from typing import Any

from shellsense.marketplace.dependency import DependencyResolver
from shellsense.marketplace.models import (
    InstallResult,
    MarketplacePlugin,
    SearchResult,
    UpdateResult,
)
from shellsense.marketplace.repository import RepositoryManager
from shellsense.marketplace.signatures import SignatureManager
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_shellsense_dir

logger = get_logger(__name__)


class MarketplaceManager:
    def __init__(
        self,
        plugin_manager: Any = None,
        enterprise_policies: Any = None,
    ) -> None:
        self.repos = RepositoryManager()
        self.signatures = SignatureManager()
        self.dep_resolver = DependencyResolver()
        self._plugin_manager = plugin_manager
        self._enterprise = enterprise_policies
        self._installed_index: dict[str, dict[str, Any]] = {}
        self._load_installed_index()

    def _index_path(self) -> str:
        return os.path.join(get_shellsense_dir(), "marketplace", "installed.json")

    def _load_installed_index(self) -> None:
        path = self._index_path()
        try:
            if os.path.isfile(path):
                with open(path) as f:
                    self._installed_index = json.load(f)
        except Exception as e:
            logger.warning("Failed to load installed index: %s", e)

    def _save_installed_index(self) -> None:
        path = self._index_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(self._installed_index, f, indent=2)
        except Exception as e:
            logger.error("Failed to save installed index: %s", e)

    def search(
        self, query: str, category: str = "", sort_by: str = "name"
    ) -> SearchResult:
        results = self.repos.search_cached(query)
        plugins = [MarketplacePlugin.from_dict(p) for p in results]

        if category:
            plugins = [p for p in plugins if category in p.categories]

        if sort_by == "name":
            plugins.sort(key=lambda p: p.name.lower())
        elif sort_by == "downloads":
            plugins.sort(key=lambda p: p.downloads, reverse=True)
        elif sort_by == "rating":
            plugins.sort(key=lambda p: p.rating, reverse=True)
        elif sort_by == "newest":
            plugins.sort(key=lambda p: p.created_at, reverse=True)

        facets: dict[str, list[str]] = {"categories": [], "tags": []}
        for p in plugins:
            for cat in p.categories:
                if cat not in facets["categories"]:
                    facets["categories"].append(cat)
            for tag in p.tags:
                if tag not in facets["tags"]:
                    facets["tags"].append(tag)

        return SearchResult(
            query=query,
            total=len(plugins),
            results=plugins,
            facets=facets,
        )

    def info(self, plugin_id: str) -> MarketplacePlugin | None:
        for repo in self.repos.list_enabled():
            data = self.repos.get_cached_plugin(repo.name, plugin_id)
            if data:
                return MarketplacePlugin.from_dict(data)
        return None

    def install(
        self, plugin_id: str, version: str = "", dry_run: bool = False
    ) -> InstallResult:
        result = InstallResult(plugin_id=plugin_id)

        plugin_data = self._find_plugin(plugin_id)
        if plugin_data is None:
            result.errors.append(f"Plugin '{plugin_id}' not found in any repository")
            return result

        plugin = MarketplacePlugin.from_dict(plugin_data)
        target_version = version or plugin.version

        if self._enterprise:
            policy = self._enterprise.check_install_policy(plugin_id)
            if not policy["allowed"]:
                result.errors.append(
                    f"Blocked by enterprise policy: {policy['reason']}"
                )
                return result

        warnings = self.signatures.verify_plugin(plugin_data)
        result.warnings.extend(warnings)
        if warnings and not dry_run:
            logger.warning("Plugin '%s' verification warnings: %s", plugin_id, warnings)

        deps = plugin.dependencies or {}
        dep_list: list[str] = list(deps.keys())
        result.dependencies = dep_list

        if dry_run:
            result.success = True
            result.version = target_version
            return result

        if self._plugin_manager:
            from shellsense.cli.commands.shared import get_plugin_manager

            pm = get_plugin_manager()

            if pm.registry.contains(plugin_id):
                result.errors.append(f"Plugin '{plugin_id}' is already installed")
                return result

            try:
                pm.install(plugin_id)
                info = pm.get_plugin(plugin_id)
                result.path = info.path
                result.version = info.version
                result.success = True

                self._installed_index[plugin_id] = {
                    "version": info.version,
                    "installed_at": __import__("datetime").datetime.now().isoformat(),
                    "repository": plugin_data.get("_repo", ""),
                }
                self._save_installed_index()
                logger.info("Installed plugin '%s' v%s", plugin_id, info.version)
            except Exception as e:
                result.errors.append(str(e))

        return result

    def remove(self, plugin_id: str) -> InstallResult:
        result = InstallResult(plugin_id=plugin_id)
        if self._plugin_manager:
            from shellsense.cli.commands.shared import get_plugin_manager

            pm = get_plugin_manager()

            if not pm.registry.contains(plugin_id):
                result.errors.append(f"Plugin '{plugin_id}' is not installed")
                return result

            try:
                pm.remove(plugin_id)
                self._installed_index.pop(plugin_id, None)
                self._save_installed_index()
                result.success = True
                logger.info("Removed plugin '%s'", plugin_id)
            except Exception as e:
                result.errors.append(str(e))
        return result

    def update(self, plugin_id: str, dry_run: bool = False) -> UpdateResult:
        result = UpdateResult(plugin_id=plugin_id)

        plugin_data = self._find_plugin(plugin_id)
        if plugin_data is None:
            result.errors.append(f"Plugin '{plugin_id}' not found")
            return result

        plugin = MarketplacePlugin.from_dict(plugin_data)
        installed = self._installed_index.get(plugin_id, {})
        old_version = installed.get("version", "")

        if not old_version:
            result.errors.append("Plugin is not installed from marketplace")
            return result

        if self._enterprise:
            policy = self._enterprise.check_install_policy(plugin_id)
            if not policy["allowed"]:
                result.errors.append(
                    f"Blocked by enterprise policy: {policy['reason']}"
                )
                return result

        result.old_version = old_version
        result.new_version = plugin.version

        if old_version == plugin.version:
            result.warnings.append("Already at latest version")
            result.success = True
            return result

        if dry_run:
            result.success = True
            return result

        try:
            from shellsense.cli.commands.shared import get_plugin_manager

            pm = get_plugin_manager()
            pm.reload(plugin_id)

            self._installed_index[plugin_id] = {
                "version": plugin.version,
                "installed_at": __import__("datetime").datetime.now().isoformat(),
                "repository": plugin_data.get("_repo", ""),
            }
            self._save_installed_index()
            result.success = True
            result.rollback_possible = True
            logger.info(
                "Updated plugin '%s': %s -> %s", plugin_id, old_version, plugin.version
            )
        except Exception as e:
            result.errors.append(str(e))

        return result

    def check_updates(self) -> list[UpdateResult]:
        results: list[UpdateResult] = []
        for plugin_id in self._installed_index:
            result = self.update(plugin_id, dry_run=True)
            if result.new_version and result.new_version != result.old_version:
                results.append(result)
        return results

    def list_installed(self) -> list[dict[str, Any]]:
        return [{"id": pid, **info} for pid, info in self._installed_index.items()]

    def sync_all(self) -> list[Any]:
        return self.repos.sync_all()

    def verify(self, plugin_id: str) -> list[str]:
        plugin_data = self._find_plugin(plugin_id)
        if plugin_data is None:
            return [f"Plugin '{plugin_id}' not found"]
        return self.signatures.verify_plugin(plugin_data)

    def export_collection(self, output_path: str) -> None:
        collection = {
            "version": "1.0",
            "exported_at": __import__("datetime").datetime.now().isoformat(),
            "plugins": self._installed_index,
        }
        with open(output_path, "w") as f:
            json.dump(collection, f, indent=2)
        logger.info("Exported plugin collection to %s", output_path)

    def import_collection(self, input_path: str) -> int:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Collection file not found: {input_path}")
        with open(input_path) as f:
            collection = json.load(f)

        imported = 0
        for plugin_id, info in collection.get("plugins", {}).items():
            if plugin_id not in self._installed_index:
                self._installed_index[plugin_id] = info
                imported += 1
        self._save_installed_index()
        logger.info("Imported %d plugins from %s", imported, input_path)
        return imported

    def _find_plugin(self, plugin_id: str) -> dict[str, Any] | None:
        for repo in self.repos.list_enabled():
            data = self.repos.get_cached_plugin(repo.name, plugin_id)
            if data:
                data["_repo"] = repo.name
                return data
        return None
